#!/usr/bin/env python
# -*- coding: utf-8 -*-

import cv2  # 图片处理三方库，用于对图片进行前后处理
import numpy as np  # 用于对多维数组进行计算
import torch  # 深度学习运算框架，此处主要用来处理数据
from mindx.sdk import Tensor  # mxVision 中的 Tensor 数据结构
from mindx.sdk import base  # mxVision 推理接口
import time
import logging

import sys
sys.path.append('camera/')
from HKcamera import getImage
from det_utils import get_labels_from_txt, letterbox, scale_coords, nms, draw_bbox  # 模型前后处理相关函数

# 导入定义的机械狗相关的包
from threading_utils.ThreadTemplates import *           # 线程的模板与基本轴指令的发送
from sendcommand import SendToCommand, heartbeat        # 发送简单指令与心跳包
from socketnetwork import network_utils                 # 通信函数
from command.udp_command import *                       # 存放各种结构体与状态数据、指令
from speeds.sportspeed import *                         # 运动精准控制的基础版模型



# 初始化日志，级别为最低级
logging.basicConfig(level=logging.DEBUG)



def Image_inference(model, labels_dict) -> list:

    try:
        while True:
            img = getImage()
            frame = img.copy()

            # 数据前处理
            img, scale_ratio, pad_size = letterbox(frame, new_shape=[640, 640])  # 对图像进行缩放与填充，保持长宽比

            # 用来存放推理结构，三个元素，[idx:识别到的序列号（指的是一次性识别到4个东西，那么序列号就是0,1,2,3），class_id:识别到的类型，pred_all[idx][4]:识别率]
            ill_sets = []

            img = img[:, :, ::-1].transpose(2, 0, 1)  # BGR to RGB, HWC to CHW
            img = np.expand_dims(img, 0).astype(np.float32)  # 将形状转换为 channel first (1, 3, 640, 640)，即扩展第一维为 batchsize
            img = np.ascontiguousarray(img) / 255.0  # 转换为内存连续存储的数组
            img = Tensor(img) # 将numpy转为转为Tensor类

            # 模型推理, 得到模型输出
            # model = base.model(modelPath=model_path, deviceId=DEVICE_ID)  # 初始化 base.model 类
            output = model.infer([img])[0]  # 执行推理。输入数据类型：List[base.Tensor]， 返回模型推理输出的 List[base.Tensor]

            # 后处理
            output.to_host()  # 将 Tensor 数据转移到 Host 侧
            output = np.array(output)  # 将数据转为 numpy array 类型
            boxout = nms(torch.tensor(output), conf_thres=0.4, iou_thres=0.5)  # 利用非极大值抑制处理模型输出，conf_thres 为置信度阈值，iou_thres 为iou阈值
            pred_all = boxout[0].numpy()  # 转换为numpy数组
            scale_coords([640, 640], pred_all[:, :4], frame.shape, ratio_pad=(scale_ratio, pad_size))  # 将推理结果缩放到原始图片大小
            # labels_dict = get_labels_from_txt('ceshi/demo_labels.txt')  # 得到类别信息，返回序号与类别对应的字典
            # img_dw = draw_bbox(pred_all, frame, (0, 255, 0), 2, labels_dict)  # 画出检测框、类别、概率
            for idx, class_id in enumerate(pred_all[:, 5]):
                # print(str(idx) + ' ' + labels_dict[int(class_id)])
                logging.info(str(idx) + ' ' + labels_dict[int(class_id)])
                # 识别率保留两位小数
                ill_sets.append([idx, int(class_id), round(pred_all[idx][4], 2)])
            
            if ill_sets == []:
                pass
            else:
                return ill_sets
            
    except KeyboardInterrupt:
        pass
    finally:
        pass

def model_init(model_path, device_id, label_path):
    # 初始化资源和变量
    base.mx_init()  # 初始化 mxVision 资源
    model = base.model(modelPath=model_path, deviceId=device_id)  # 初始化 base.model 类
    labels_dict = get_labels_from_txt(label_path)  # 得到类别信息，返回序号与类别对应的字典
    return model, labels_dict
                        


if __name__ == "__main__":

    # 变量初始化
    DEVICE_ID = 0                                                   # 设备id
    model_path = 'smart_logistics_models/1.om'                      # 模型路径
    label_path = 'smart_logistics_models/predefined_classes.txt'    # 标签地址

    # 模型与标签txt的初始化
    model, labels_dict = model_init(model_path, DEVICE_ID, label_path)

    # 建立通讯
    sfd, target_address = network_utils.setup_socket_and_address()

    # 建立心跳包线程，按照心跳函数中的频率发送心跳包
    heartbeat_thread = MyRepeatThread("HeartbeatThread", heartbeat.send_udp_heartbeat, 0.25, None, sfd, target_address)
    heartbeat_thread.start()

    # 站立指令
    SendToCommand.perform_action(sfd, target_address, 0x21010202, 0, 0)

    # 创建一个简单指令的结构体实例
    action_CommandHead = CommandHead()

    verifications = 0  # 进入狗动作的标志位
    list0 = []         # 存放物品值的列表
    k = 0              # 计数


    while True:
        ill_sets = Image_inference(model, labels_dict)
        print("ill_sets：", ill_sets)
        list0.append(ill_sets[0][1])
        k += 1
        if k == 3:
            # 将列表转换为集合，集合中的元素都是唯一的
            unique_elements = set(list0)
            
            # 如果集合中的元素个数为1，则表示列表中的三个元素都相同
            if len(unique_elements) == 1:
                verifications = 1  # 当连续三次都是统一个手势，标志位归1，进入到动作循环中
                k, list0 = 0, []               # 归0，重新计数
                object_class = ill_sets[0][1]
            else:
                k, list0 = 0, []
                pass


        while verifications:
            # 分别为4个位置的实际位置，第一位数填角度，第二个填写距离（单位m），例如：[[30,0,3],...] 表示右转30度，直走0.3m
            Target_location = [[0, 1.5], [45, 1.0], [0, 0.9], [45, 0.6]]
            # 第一类是蔬菜，第二类是机械，第三类是饮品，第四类是家具

            # 根据物品的种类来定义应该走向哪一个区域
            actions_params = {
                1: [(Target_location[object_class][1], )],  # 使用速度默认值 
                3: [(Target_location[object_class][0],)]
            }
            actions_sequence = [(3, 0),(1,0)]  # (动作ID, 参数列表索引，先转弯，再前进)



            # 定义返回起点的逻辑
            if Target_location[object_class][0] == 0:
                Target_location_return = [180, Target_location[object_class][1], -180]
            elif 0 < Target_location[object_class][0] <= 90:
                Target_location_return = [180, Target_location[object_class][1], (90+Target_location[object_class][0])]
            elif 90 < Target_location[object_class][0] <= 180:
                Target_location_return = [180, Target_location[object_class][1], (180-Target_location[object_class][0])]
            elif -90 < Target_location[object_class][0] < 0:
                Target_location_return = [180, Target_location[object_class][1], -(90+abs(Target_location[object_class][0]))]    
            elif -180 < Target_location[object_class][0] <= -90:
                Target_location_return = [180, Target_location[object_class][1], -(180-abs(Target_location[object_class][0]))]
            print(Target_location_return)
            actions_params_return = {
                3: [(Target_location_return[0], ), (Target_location_return[2], )],
                1: [(Target_location_return[1], )],
            }
            actions_sequence_return = [(3, 0), (1, 0), (3, 1)]

            for action_id, params_index in actions_sequence:
                action_func = actions_dict.get(action_id, None)
                if action_func:
                    # 从actions_params中获取指定动作ID和参数索引对应的参数
                    params = actions_params[action_id][params_index]
                    logging.info('------------------------------------------------------------------------------------------------------------------')
                    logging.info(f'action_func: {action_func}')
                    logging.info(f'params: {params}')
                    if isinstance(params, tuple):
                        # 调用动作函数，提供已知参数，允许函数使用默认参数值完成调用
                        thread = action_func(*params)  # 正确# 展开参数列表并传递给函数
                        thread.start()
                        thread.join()
                        time.sleep(1)

            time.sleep(5)            

            for action_id, params_index in actions_sequence_return:
                action_func = actions_dict.get(action_id, None)
                if action_func:
                    # 从actions_params中获取指定动作ID和参数索引对应的参数
                    params = actions_params_return[action_id][params_index]
                    logging.info('------------------------------------------------------------------------------------------------------------------')
                    logging.info(f'action_func: {action_func}')
                    logging.info(f'params: {params}')
                    if isinstance(params, tuple):
                        # 调用动作函数，提供已知参数，允许函数使用默认参数值完成调用
                        thread = action_func(*params)  # 正确# 展开参数列表并传递给函数
                        thread.start()
                        thread.join()
                        time.sleep(1)


            verifications = 0 # 动作结束，跳出循环，重新开始识别
            break

















