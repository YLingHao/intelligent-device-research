#!/usr/bin/env python
# -*- coding: utf-8 -*-

import cv2
import time

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
from HandDistance.ridge_np import *                     # 测量距离

def save_image(img):

    picutre_name = str(time.time()).split('.')
    picutre_name = picutre_name[0] + picutre_name[1]
    
    dir = 'three2'
    
    image_name = f'/opt/Dog/UDPControl/train_gesture/{dir}/{picutre_name}.jpg'
    cv2.imwrite(image_name, img)
    print(f"图像已保存为: {picutre_name}")

print("按 's' 保存图像，按 'q' 退出程序。")

# 主循环
while True:
    img = getImage()  # 获取图像

    cv2.imshow('Camera Feed', img)  # 显示图像
    key = cv2.waitKey(1) & 0xFF  # 检测按键事件

    if key == ord('s'):
        save_image(img)  # 保存图像
    elif key == ord('q'):
        break  # 退出循环

# 清理工作
cv2.destroyAllWindows()