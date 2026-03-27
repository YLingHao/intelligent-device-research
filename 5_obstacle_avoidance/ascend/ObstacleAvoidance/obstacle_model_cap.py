#!/usr/bin/env python
# -*- coding: utf-8 -*-
import cv2  # 导入OpenCV库，用于图像处理
import numpy as np  # 导入NumPy库，用于对多维数组进行计算
import torch  # 导入PyTorch库，用于深度学习运算
from mindx.sdk import Tensor  # 从MindX SDK导入Tensor数据结构
from mindx.sdk import base  # 从MindX SDK导入基础推理接口
import time  # 导入time模块，用于时间相关的操作
import logging  # 导入logging库，用于日志记录
import threading  # 导入threading库，用于多线程操作
from typing import *  # 导入typing模块，用于类型注解
import sys  # 导入sys库，用于系统相关操作
sys.path.append('camera/')  # 将'camera'目录添加到模块搜索路径
from HKcamera import getImage  # 从HKcamera模块导入getImage函数，用于获取图像
from det_utils import get_labels_from_txt, letterbox, scale_coords, nms, draw_bbox  # 从det_utils模块导入相关函数

# 初始化日志，设置日志级别为DEBUG
logging.basicConfig(level=logging.DEBUG)

# 定义Image_inference函数，用于执行图像推理
def Image_inference(model, labels_dict):
    try:
        img = getImage()  # 获取图像
        frame = img.copy()  # 复制图像用于后续处理
        # 使用letterbox函数对图像进行尺寸调整和填充
        img, scale_ratio, pad_size = letterbox(frame, new_shape=[640, 640])
        ill_sets = []  # 初始化用于存储检测结果的列表
        # 对图像进行格式转换和归一化处理，准备输入到模型中
        img = img[:, :, ::-1].transpose(2, 0, 1)
        img = np.expand_dims(img, 0).astype(np.float32)
        img = np.ascontiguousarray(img) / 255.0
        img = Tensor(img)
        # 使用模型进行推理
        output = model.infer([img])[0]
        output.to_host()  # 将推理结果从设备传输到主机
        output = np.array(output)  # 将推理结果转换为NumPy数组
        # 使用nms函数进行非极大值抑制处理
        boxout = nms(torch.tensor(output), conf_thres=0.7, iou_thres=0.5)
        # 将nms处理后的预测结果转换为NumPy数组
        pred_all = boxout[0].numpy()
        # 调整坐标点以适应原始图像尺寸
        scale_coords([640, 640], pred_all[:, :4], frame.shape, ratio_pad=(scale_ratio, pad_size))
        # 遍历预测结果，提取类别和置信度信息
        for idx, class_id in enumerate(pred_all[:, 5]):
            # 记录检测到的类别、类别ID和置信度
            ill_sets.append([labels_dict[int(class_id)], int(class_id), round(pred_all[idx][4], 2)])
        # 返回检测结果列表
        return ill_sets
    except KeyboardInterrupt:
        # 如果发生键盘中断（Ctrl+C），返回空列表
        return []

# 定义model_init函数，用于初始化模型和标签字典
def model_init(model_path, device_id, label_path):
    base.mx_init()  # 初始化MindX SDK
    model = base.model(modelPath=model_path, deviceId=device_id)  # 加载模型
    labels_dict = get_labels_from_txt(label_path)  # 从标签文件中获取类别标签
    return model, labels_dict  # 返回模型和标签字典

def inference_loop(result, result_lock):
    # 初始化一个空列表，用于存储推理结果
    list0 = []
    # 初始化计数器
    k = 0

    # 设备ID设置为0
    DEVICE_ID = 0
    # 模型路径设置为 'smart_logistics_models/1.om'
    model_path = 'avoidance_models/1.om'
    # 标签文件路径设置为 'smart_logistics_models/predefined_classes.txt'
    label_path = 'avoidance_models/predefined_classes.txt'
    # 调用 model_init 函数初始化模型和标签字典
    model, labels_dict = model_init(model_path, DEVICE_ID, label_path)

    try:
        # 进入一个无限循环，持续进行推理
        while True:
            # 调用 Image_inference 函数进行图像推理，并获取结果
            ill_sets = Image_inference(model, labels_dict)
            # 如果推理结果为空，继续下一次循环
            if not ill_sets:
                continue
            # 将推理结果中的第一个元素添加到列表 list0 中
            list0.append(ill_sets[0][1])
            # 计数器 k 加 1
            k += 1

            # 如果计数器 k 等于 2，表示已经收集到两个连续的推理结果
            if k == 2:
                # 创建一个集合，用于存储 list0 中的唯一元素
                unique_elements = set(list0)
                # 如果集合的长度为 1，表示两次推理结果相同
                if len(unique_elements) == 1:
                    # 将对象类别设置为 list0 中的第一个元素
                    object_class = ill_sets[0][0]
                    # 重置计数器 k 和 list0
                    k, list0 = 0, []
                    # 使用结果锁进行线程安全操作
                    with result_lock:
                        # 清空结果列表
                        result.clear()
                        # 将新的结果添加到结果列表中
                        result.append(object_class)
                        # 打印当前结果
                        print('result:', result)
                # 如果集合长度不为 1，表示两次推理结果不一致
                else:
                    # 设置 object_class 为 None
                    object_class = None
                    # 重置计数器 k 和 list0
                    k, list0 = 0, []
    # 如果捕获到 KeyboardInterrupt 异常（例如使用 Ctrl+C），不执行任何操作
    except KeyboardInterrupt:
        pass