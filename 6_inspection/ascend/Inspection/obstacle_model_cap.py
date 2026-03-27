#!/usr/bin/env python
# -*- coding: utf-8 -*-

import cv2  # 图片处理三方库，用于对图片进行前后处理
import numpy as np  # 用于对多维数组进行计算
import torch  # 深度学习运算框架，此处主要用来处理数据
from mindx.sdk import Tensor  # mxVision 中的 Tensor 数据结构
from mindx.sdk import base  # mxVision 推理接口
import time
import logging
import threading
from typing import *
import sys
sys.path.append('camera/')
from HKcamera import getImage
from det_utils import get_labels_from_txt, letterbox, scale_coords, nms, draw_bbox  # 模型前后处理相关函数


# 初始化日志，级别为最低级
logging.basicConfig(level=logging.DEBUG)


def Image_inference(model, labels_dict):
    try:
        img = getImage()
        frame = img.copy()
        img, scale_ratio, pad_size = letterbox(frame, new_shape=[640, 640])
        ill_sets = []
        img = img[:, :, ::-1].transpose(2, 0, 1)
        img = np.expand_dims(img, 0).astype(np.float32)
        img = np.ascontiguousarray(img) / 255.0
        img = Tensor(img)
        output = model.infer([img])[0]
        output.to_host()
        output = np.array(output)
        boxout = nms(torch.tensor(output), conf_thres=0.7, iou_thres=0.5)
        pred_all = boxout[0].numpy()
        scale_coords([640, 640], pred_all[:, :4], frame.shape, ratio_pad=(scale_ratio, pad_size))

        for idx, class_id in enumerate(pred_all[:, 5]):
            # logging.info(str(idx) + ' ' + labels_dict[int(class_id)])
            ill_sets.append([labels_dict[int(class_id)], int(class_id), round(pred_all[idx][4], 2)])

        return ill_sets
    except KeyboardInterrupt:
        return []

def model_init(model_path, device_id, label_path):
    base.mx_init()
    model = base.model(modelPath=model_path, deviceId=device_id)
    labels_dict = get_labels_from_txt(label_path)
    return model, labels_dict




def inference_loop(result, result_lock):
    list0 = []
    k = 0

    DEVICE_ID = 0
    model_path = 'avoidance_models/1.om'
    label_path = 'avoidance_models/predefined_classes.txt'
    model, labels_dict = model_init(model_path, DEVICE_ID, label_path)  

    try:
        while True:
            ill_sets = Image_inference(model, labels_dict)
            if not ill_sets:
                continue
            # print("ill_sets:", ill_sets)
            list0.append(ill_sets[0][1])
            k += 1

            if k == 2:
                unique_elements = set(list0)
                if len(unique_elements) == 1:
                    object_class = ill_sets[0][0]
                    k, list0 = 0, []
                    with result_lock:
                        result.clear()  # Clear the list in place
                        result.append(object_class)  # Append the new result
                        print('result:', result)
                else:
                    object_class = None
                    k, list0 = 0, []

    except KeyboardInterrupt:
        pass




    
