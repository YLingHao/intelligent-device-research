#!/usr/bin/env python
# -*- coding: utf-8 -*-

import cv2  # 图片处理三方库，用于对图片进行前后处理

import logging
from cvzone.HandTrackingModule import HandDetector

import sys
sys.path.append('camera/')
from HKcamera import getImage
# from det_utils import get_labels_from_txt, letterbox, scale_coords, nms, draw_bbox  # 模型前后处理相关函数

# 导入定义的机械狗相关的包
from threading_utils.ThreadTemplates import *           # 线程的模板与基本轴指令的发送
from sendcommand import SendToCommand, heartbeat        # 发送简单指令与心跳包
from socketnetwork import network_utils                 # 通信函数
from command.udp_command import *                       # 存放各种结构体与状态数据、指令
from speeds.sportspeed import *                         # 运动精准控制的基础版模型
from robotstatuswatcher.listener import *               # 监听机械狗状态
from HandDistance.ridge_np import *                     # 测量距离


# 实例化手部检测器
detector = HandDetector(detectionCon=0.8, maxHands=2)

# 初始化日志，级别为最低级
logging.basicConfig(level=logging.DEBUG)

actions_dict = {
    1: action_go_straight,
    2: action_revolve_left_and_right,
}


# 建立通讯
sfd, target_address = network_utils.setup_socket_and_address()

# 建立心跳包线程，按照心跳函数中的频率发送心跳包
heartbeat_thread = MyRepeatThread("HeartbeatThread", heartbeat.send_udp_heartbeat, 0.25, None, sfd, target_address)
heartbeat_thread.start()

# 站立指令
SendToCommand.perform_action(sfd, target_address, 0x21010202, 0, 0)
time.sleep(3)


# 标志位
HKflag = 1
Dogflag = 0
while True:
    while HKflag:
        img = getImage()
        # 这个的 draw = False 是指只显示实际距离的检测框，手部的检测框不显示
        hands, img = detector.findHands(img, draw=False)
        # print(hands)
        list0 = []
        if hands:
            lmList = hands[0]['lmList']
            # print(hands[0]['type'])
            x,y,w,h = hands[0]['bbox']

            x1, y1, z1 = lmList[5]
            x2, y2, z2 = lmList[17]
            x3, y3, z3 = lmList[0]
            x4, y4, z4 = lmList[12]

            angle_xy = predict_angle(hands[0]['center'][0], hands[0]['center'][1])
            distanceCM = predict_distance(x1, x2, x3, x4, y1, y2, y3, y4)
            # print('angle_xy, distanceCM', angle_xy, distanceCM)
            angle = angle_xy[0]

            # if abs(angle) > 10 and abs(distanceCM)>10:
            if abs(distanceCM)>10:
                HKflag = 0
                Dogflag = 1
                # print('HKflag, Dogflag', HKflag, Dogflag)
                # print('角度和距离：', angle, distanceCM)
                break


    while Dogflag:
            logging.info('---------------进入狗循环中-----------------')

            # 动作ID与对应参数的映射
            actions_params = {
                1: [(distanceCM/100,)],  # 给出必须参数，使用速度默认值 
                2: [(angle,)]
            }

            # 示例动作顺序列表，可能包括时同一动作多次但参数不同
            actions_sequence = [(2, 0),(1,0)]  # (动作ID, 参数列表索引，先转弯，再前进)

            # 执行动作
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
                        
                    else:
                        logging.error('params 必须是一个 tuple 或者 列表')
            
            HKflag = 1
            Dogflag = 0

    cv2.destroyAllWindows()