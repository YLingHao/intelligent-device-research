#!/usr/bin/env python
# -*- coding: utf-8 -*-

import cv2
import numpy as np
from matplotlib import pyplot as plt
import math
from contextlib import ExitStack
import os
import sys
import datetime
sys.path.append('camera/')
from HKcamera import getImage

# 导入定义的机械狗相关的包
from threading_utils.ThreadTemplates import *           # 线程的模板与基本轴指令的发送
from sendcommand import SendToCommand, heartbeat        # 发送简单指令与心跳包
from socketnetwork import network_utils                 # 通信函数
from command.udp_command import *                       # 存放各种结构体与状态数据、指令
from speeds.sportspeed import *                         # 运动精准控制的基础版模型
from robotstatuswatcher.listener import *               # 监听机械狗状态
from HandDistance.ridge_np import *                     # 测量距离
from obstacle_model_cap import *                        # 识别障碍物
from image_processing import *                          # 分析与计算仪表盘温度

# 建立通讯
sfd, target_address = network_utils.setup_socket_and_address()

# 建立心跳包线程，按照心跳函数中的频率发送心跳包
heartbeat_thread = MyRepeatThread("HeartbeatThread", heartbeat.send_udp_heartbeat, 0.25, None, sfd, target_address)
heartbeat_thread.start()

# 站立
SendToCommand.perform_action(sfd, target_address, 0x21010202, 0, 0)
time.sleep(1)
# SendToCommand.perform_action(sfd, target_address, 0x21010300, 0, 0)
SendToCommand.perform_action(sfd, target_address, 0x21010D06, 0, 0) # 移动模式
time.sleep(1)
# 开启雷达
SendToCommand.perform_action(sfd, target_address, 0x21012109, 0x40, 0)

# 全局变量和锁
status_list = []
status_list_lock = threading.Lock()
result = []
result_lock = threading.Lock()

# 开始雷达监听和识别模型的线程
radar_thread = threading.Thread(target=status_listener_radar, args=(status_list, status_list_lock))
radar_thread.start()
picture_thread = threading.Thread(target=inference_loop, args=(result, result_lock))
picture_thread.start()

# 创建一个全局的 Event 对象用于控制线程暂停和继续
pause_event = threading.Event()
pause_event.set()  # 初始状态为设置，表示不暂停

# 避障的次数
obstacle = 0
staircase = 0
hole = 0

# 避障的距离限制
obs_void_distance = 0.4

# 固定路线
actions_params = {
    1: [(1.6,), (0.8,)],  
    3: [(90,), (-90,)]
}
actions_sequence = [(3, 0), (1, 0), (3, 1), (1, 1)]

# 更新后的路线
updated_actions_params = actions_params.copy()

# 避障路线
avoid_actions_params = {
    1: [(0.7,), (0.8,)], 
    3: [(-46.0,), (91.0,), (-30.0,)]
}
avoid_actions_sequence = [(3, 0), (1, 0), (3, 1), (1, 1), (3, 2)] 

# 仪表盘的路线
dashboard_actions_params = {
    1: [(0.6,) ],
    }
dashboard_actions_sequence = [(1, 0)]


# 循环控制变量
continue_loop = True

# 记录队列的角标
sequence_index = 0

# 识别仪表盘的标志位
flag = 1

# 用于存储检测到的圆的信息
detected_circles = []


def execute_avoid_sequence(params = avoid_actions_params, sequence = avoid_actions_sequence):
    logging.info("进入 execute_avoid_sequence")
    logging.info("--------params--------: %s", params)
    for action_id, params_index in sequence:
        action_func = actions_dict.get(action_id, None)
        if action_func:
            avoid_params = params[action_id][params_index]
            if isinstance(avoid_params, tuple):
                avoid_thread = action_func(*avoid_params)
                avoid_thread.start()
                avoid_thread.join()
                time.sleep(1)
    logging.info("离开 execute_avoid_sequence")

def update_route_params(thread, params, before_long, temp):
    # global updated_actions_params
    # 更新机器狗的行走路线参数
    # 这里updated_actions_params是全局变量，存储更新后的路线参数
    # 获取当前动作序列的索引和键
    current_params_index = actions_sequence[sequence_index]
    current_params_key, current_params_index = actions_sequence[sequence_index][0], actions_sequence[sequence_index][1]
    # 更新路线参数，计算新的行走距离
    updated_actions_params[current_params_key][current_params_index] = (params[0] - before_long - temp,)
    logging.info(f'更新后的路线updated_actions_params: {updated_actions_params}')


def handle_obstacles(thread, params):
    # 定义全局变量
    global continue_loop, obstacle
    # 如果未遇到障碍物，并且状态列表中有数据，并且距离小于等于避障距离限制
    if obstacle == 0 and status_list and status_list[3] <= obs_void_distance:
        # 增加障碍物计数
        obstacle += 1
        # 执行直线前进动作，参数为长距离，当前时间，避障距离限制
        before_long = go_straight(long=9999, times=thread.print_attributes()['current_time_start'], obs_void_distance=obs_void_distance)                    
        # 计算临时变量
        temp = 2 * avoid_actions_params[1][0][0] / math.sqrt(2)
        # 更新路线参数
        update_route_params(thread, params, before_long, temp)
        # 停止当前线程
        thread.stop()
        thread.join()
        # 打印停止信息
        logging.info('原始路线停止。')
        # 如果线程已停止
        if thread._is_stopped:
            # 执行避障序列
            execute_avoid_sequence()
        # 重置动作参数和序列
        global actions_params, actions_sequence
        actions_params = updated_actions_params
        actions_sequence = actions_sequence[sequence_index:]
        # 设置循环控制变量为True，继续执行
        continue_loop = True
        # 清除暂停事件
        pause_event.clear()


def handle_staircases():
    # 定义全局变量
    global staircase
    # 如果未遇到楼梯，并且结果列表为['staircase']，表示检测到楼梯
    if staircase == 0 and result == ['staircase']:
        # 增加楼梯计数
        staircase += 1
        # 打印检测到楼梯的信息
        logging.info("Detected 'staircase', pausing thread.")
        # 发送指令以暂停机械狗
        SendToCommand.perform_action(sfd, target_address, 0x21010407, 0, 0)


def handle_holes():
    # 定义全局变量
    global hole
    # 如果未遇到坑洞，并且结果列表为['hole'], 表示检测到狗洞
    if hole == 0 and result == ['hole']:
        # 增加狗洞计数
        hole += 1
        # 打印检测到狗洞的信息
        logging.info("Detected 'hole', pausing thread.")
        # 发送指令以暂停机械狗
        SendToCommand.perform_action(sfd, target_address, 0x21010406, 0, 0)


def handle_status():
    # 定义全局变量
    global hole
    # print(status_listener())
    if status_listener() == [6, 13, 1]:  # 力控状态（静止站立）且步态为高踏步越障步态
        SendToCommand.perform_action(sfd, target_address, 0x21010300, 0, 0)
        time.sleep(1)
    elif status_listener() == [6, 0, 1] and hole == 1:  # 正在以平地低速步态踏步（匍匐状态）
        # 增加坑洞计数  
        hole += 1
        SendToCommand.perform_action(sfd, target_address, 0x21010406, 0, 0)
        time.sleep(1)


output_folder = '/opt/Dog/UDPControl/dashboarddata'
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

while continue_loop:
    time.sleep(1)

    if flag:
        # 前进走到仪表盘的前方
        for action_id, params_index in dashboard_actions_sequence:
            action_func = actions_dict.get(action_id, None)
            if action_func:
                params = dashboard_actions_params[action_id][params_index]
                print("params:", params)
                if isinstance(params, tuple):
                    thread = action_func(*params)
                    thread.start()
                    thread.join()
                    time.sleep(3)
                    time1 = time.monotonic()

        SendToCommand.perform_action(sfd, target_address, 0x21010D05, 0, 0) # 原地模式
        # 调整俯仰角
        ACTION_Adjust_the_pitch_angle = MyRepeatThread("ACTION_Adjust_the_pitch_angle", SendToCommand.perform_action, 
                0.1, 5, sfd, 
                target_address, 
                0x21010130, 30000, 0)
        ACTION_Adjust_the_pitch_angle.start()
        
        # 首先进入到仪表盘的是识别
        while flag:
            frame = getImage()
            if frame is None:
                print("No image captured")
                continue

            largest_circle = detect_largest_circle(frame)
            if largest_circle is not None:
                # 将检测到的圆信息存储到列表中
                detected_circles.append(largest_circle)
                
                # 保留最新的10个圆的信息
                if len(detected_circles) > 10:
                    detected_circles.pop(0)
                    
                # 计算圆的平均中心位置和半径
                avg_circle = np.mean(detected_circles, axis=0).astype(int)
                
                cv2.circle(frame, (avg_circle[0], avg_circle[1]), avg_circle[2], (100, 255, 100), 3)
                cv2.circle(frame, (avg_circle[0], avg_circle[1]), int(avg_circle[2] * inner_circle_scale), (255, 0, 0), 2)
                
                lines = detect_lines_in_circle(frame, avg_circle, max_line_length)
                if lines is not None:
                    for line in lines:
                        x1, y1, x2, y2 = line[0]
                        cv2.line(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                        # # 在起点画蓝色点
                        cv2.circle(frame, (x1, y1), 5, (255, 0, 0), -1)

                        # # 在终点画红色点
                        cv2.circle(frame, (x2, y2), 5, (0, 0, 255), -1)

                        # # 在直线的中点画上点
                        # cv2.circle(frame, ((x1+x2)//2, (y1+y2)//2), 5, (100, 30, 100), -1)

                        # 得到温度
                        temperature = calculate_temperature(avg_circle, x1, y1, x2, y2)
                        font = cv2.FONT_HERSHEY_SIMPLEX
                        cv2.putText(frame, f'temperature: {temperature:.2f} C', (10, 60), font, 1, (200, 25, 60), 1, cv2.LINE_AA)
                        print(f"温度: {temperature} 度")
                        num_lines = len(lines)

                        # 如果检测到一条直线，则保存图像
                        if num_lines == 1:
                            now = datetime.datetime.now()
                            formatted_now = now.strftime("%Y-%m-%d %H:%M:%S")
                            # print("Formatted Date and Time:", formatted_now)
                            filename = os.path.join(output_folder, f'{formatted_now}_温度:{temperature:.2f}°C.png')
                            cv2.imwrite(filename, frame)
                            print(f'Image saved to {filename}')
                            ACTION_Adjust_the_pitch_angle.join()
                            time.sleep(3)
                            SendToCommand.perform_action(sfd, target_address, 0x21010D06, 0, 0)  # 移动模式
                            flag = 0
                        
                        elif time.monotonic() - time1 > 6:
                            SendToCommand.perform_action(sfd, target_address, 0x21010D06, 0, 0)  # 移动模式
                            logging.info('未识别到仪表盘！')
                            flag = 0
                            time.sleep(3)

                        if cv2.waitKey(1) & 0xFF == ord('q'):
                            break

        cv2.destroyAllWindows()


    continue_loop = False
    for action_id, params_index in actions_sequence:
        action_func = actions_dict.get(action_id, None)

        if action_func:
            params = actions_params[action_id][params_index]
            logging.info(f'params: {params}')

            if isinstance(params, tuple):
                thread = action_func(*params)
                thread.start()
                while thread.is_alive():
                    with ExitStack() as stack:
                        stack.enter_context(status_list_lock)
                        stack.enter_context(result_lock)
                        handle_obstacles(thread, params)
                        handle_staircases()
                        handle_holes()

                if not continue_loop:
                    sequence_index += 1  # 成功走完一个，队列角标加一
                    thread.join()
                    handle_status()

                if continue_loop:
                    break
            time.sleep(1)
