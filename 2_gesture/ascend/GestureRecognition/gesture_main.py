#!/usr/bin/env python
# -*- coding: utf-8 -*-

import cv2  # 图片处理三方库，用于对图片进行前后处理
import numpy as np  # 用于对多维数组进行计算
import torch  # 深度学习运算框架，此处主要用来处理数据
from mindx.sdk import Tensor  # mxVision 中的 Tensor 数据结构
from mindx.sdk import base  # mxVision 推理接口
import time
import logging
from typing import *
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
from robotstatuswatcher.listener import *               # 监听机械狗状态


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

def model_init(model_path, device_id, label_path) -> Tuple['base.model', Dict[int, str]]:
    # 初始化资源和变量
    base.mx_init()  # 初始化 mxVision 资源
    model = base.model(modelPath=model_path, deviceId=device_id)  # 初始化 base.model 类
    labels_dict = get_labels_from_txt(label_path)  # 得到类别信息，返回序号与类别对应的字典
    return model, labels_dict

if __name__ == "__main__":

    # 建立通讯
    sfd, target_address = network_utils.setup_socket_and_address()

    # 建立心跳包线程，按照心跳函数中的频率发送心跳包
    heartbeat_thread = MyRepeatThread("HeartbeatThread", heartbeat.send_udp_heartbeat, 0.25, None, sfd, target_address)
    heartbeat_thread.start()

    # 站立指令
    SendToCommand.perform_action(sfd, target_address, 0x21010202, 0, 0)

    # 变量初始化
    DEVICE_ID = 0                                           # 设备id
    model_path = 'gesture_models/gesture.om'                # 模型路径
    label_path = 'gesture_models/predefined_classes.txt'    # 标签地址

    # 模型与标签txt的初始化
    model, labels_dict = model_init(model_path, DEVICE_ID, label_path)

    # 创建一个简单指令的结构体实例
    action_CommandHead = CommandHead()

    verifications = 0  # 进入狗动作的标志位
    list0 = []         # 存放手势值的列表
    k = 0              # 计数
    while True:
        ill_sets = Image_inference(model, labels_dict)
        print("ill_sets：", ill_sets)
        # print('ill_sets的长度：', len(ill_sets))
        list0.append(ill_sets[0][1])
        k += 1
        if k == 3:
            # 将列表转换为集合，集合中的元素都是唯一的
            unique_elements = set(list0)
            
            # 如果集合中的元素个数为1，则表示列表中的三个元素都相同
            if len(unique_elements) == 1:
                verifications = 1  # 当连续三次都是统一个手势，标志位归1，进入到动作循环中
                k, list0 = 0, []               # 归0，重新计数
            else:
                k, list0 = 0, []
                pass
        
        while verifications:
            for ill_set in ill_sets:
                # 只执行接受到的第一个动作手势，不接受其他的同时执行两个
                if ill_set[0] == 0:
                    # print("ill_set的第一个值：",ill_set)
                    if ill_set[1] == 2: # 'fist' 趴下 ACTION_STAND_DOWN
                        if status_listener() == [6, 0, 0]: # 监听当前是否是站立状态，站立状态满足趴下动作
                            action_CommandHead.code = dog_actions.get("ACTION_STAND_DOWN")
                            SendToCommand.perform_action(sfd, target_address, action_CommandHead.code, action_CommandHead.parameters_size,action_CommandHead.type_)
                            
                            while 1:
                                if status_listener() == [1, 0, 0]: # 监听当前是否是趴下动作
                                    print("趴下成功！")
                                    time.sleep(5)
                                    SendToCommand.perform_action(sfd, target_address, 0x21010202, 0, 0)
                                    verifications = 0 # 动作结束，跳出循环，重新开始识别
                                    break
                        
                    elif ill_set[1] == 7: # 'one' 扭身跳 ACTION_TWIST_JUMP
                        if status_listener() == [6, 0, 0]: # 监听当前是否是站立状态，站立状态满足扭身跳动作
                            action_CommandHead.code = dog_actions.get("ACTION_TWIST_JUMP")
                            SendToCommand.perform_action(sfd, target_address, action_CommandHead.code, action_CommandHead.parameters_size,action_CommandHead.type_)
                            while 1:
                                if status_listener() == [6, 0, 4]:# 监听当前是否是扭身跳动作
                                    print("扭身跳！")
                                    verifications = 0 # 动作结束，跳出循环，重新开始识别
                                    break
                    
                    elif ill_set[1] == 9: # 'peace' 扭身体 ACTION_TWIST_BODY
                        if status_listener() == [6, 0, 0]: # 监听当前是否是站立状态，站立状态满足扭身体动作
                            action_CommandHead.code = dog_actions.get("ACTION_TWIST_BODY")
                            SendToCommand.perform_action(sfd, target_address, action_CommandHead.code, action_CommandHead.parameters_size,action_CommandHead.type_)
                            while 1:
                                if status_listener() == [6, 0, 2]:# 监听当前是否是扭身体动作
                                    print("扭身体！")
                                    verifications = 0 # 动作结束，跳出循环，重新开始识别
                                    break
                    
                    elif ill_set[1] == 10: # 'rock' 太空步 ACTION_MOONWALK
                        if status_listener() == [6, 0, 0]: # 监听当前是否是站立状态，站立状态满足太空步动作
                            action_CommandHead.code = dog_actions.get("ACTION_MOONWALK")
                            SendToCommand.perform_action(sfd, target_address, action_CommandHead.code, action_CommandHead.parameters_size,action_CommandHead.type_)
                            while 1:
                                if status_listener() == [6, 12, 1]:# 监听当前是否是扭身跳动作
                                    print("太空步")
                                    time.sleep(4)
                                    SendToCommand.perform_action(sfd, target_address, 0x21010202, 0, 0)
                                    verifications = 0 # 动作结束，跳出循环，重新开始识别
                                    break

                    elif ill_set[1] == 16: # 'three2' 打招呼 ACTION_GREET
                        if status_listener() == [6, 0, 0]: # 监听当前是否是站立状态，站立状态满足打招呼动作
                            action_CommandHead.code = dog_actions.get("ACTION_GREET")
                            SendToCommand.perform_action(sfd, target_address, action_CommandHead.code, action_CommandHead.parameters_size,action_CommandHead.type_)
                            while 1:
                                if status_listener() == [20, 0, 0]:# 监听当前是否是打招呼动作
                                    print("打招呼")
                                    verifications = 0 # 动作结束，跳出循环，重新开始识别
                                    break

                    elif ill_set[1] not in [2, 7, 9, 10, 16]:
                        logging.info("手势不在动作集合中，请重新做动作")
                        verifications = 0 # 动作结束，跳出循环，重新开始识别

                        
                    