
#!/usr/bin/env python
# -*- coding: utf-8 -*-


import threading
import time
import logging
import math
from contextlib import ExitStack

# 导入定义的机械狗相关的包
from threading_utils.ThreadTemplates import *  # 线程的模板与基本轴指令的发送
from sendcommand import SendToCommand, heartbeat  # 发送简单指令与心跳包
from socketnetwork import network_utils  # 通信函数
from command.udp_command import *  # 存放各种结构体与状态数据、指令
from speeds.sportspeed import *  # 运动精准控制的基础版模型
from robotstatuswatcher.listener import *  # 监听机械狗状态
from HandDistance.ridge_np import *  # 测量距离
from obstacle_model_cap import *    

# 初始化日志，级别为最低级
logging.basicConfig(level=logging.DEBUG)

# 全局变量和锁
status_list = []
status_list_lock = threading.Lock()
result = []
result_lock = threading.Lock()

# 避障的距离限制
obs_void_distance = 0.4

# 固定路线
actions_params = {
    1: [(2,), (1.1,)],  
    3: [(90,)]
}
actions_sequence = [(1, 0), (3, 0), (1, 1)]

# 避障路线
avoid_actions_params = {
    1: [(0.7,), (0.7,)], 
    3: [(-46.0,), (91.0,), (-30.0,)]
}
avoid_actions_sequence = [(3, 0), (1, 0), (3, 1), (1, 1), (3, 2)] 

# 更新后的路线
updated_actions_params = actions_params.copy()

# 避障次数
obstacle = 0
staircase = 0
hole = 0

# 记录队列的角标
sequence_index = 0

# 循环控制变量
continue_loop = True

# 创建一个全局的 Event 对象用于控制线程暂停和继续
pause_event = threading.Event()
pause_event.set()  # 初始状态为设置，表示不暂停


def initialize_communication():
    # 设置网络通信，初始化套接字和目标地址
    sfd, target_address = network_utils.setup_socket_and_address()
    # 创建并启动心跳包发送线程
    heartbeat_thread = MyRepeatThread("HeartbeatThread", heartbeat.send_udp_heartbeat, 0.25, None, sfd, target_address)
    heartbeat_thread.start()
    # 返回套接字和目标地址
    return sfd, target_address


def initialize_threads():
    # 向机器狗发送指令以开启雷达
    SendToCommand.perform_action(sfd, target_address, 0x21012109, 0x40, 0)
    # 创建雷达状态监听线程并启动
    radar_thread = threading.Thread(target=status_listener_radar, args=(status_list, status_list_lock))
    radar_thread.start()
    # 创建图像识别处理线程并启动
    picture_thread = threading.Thread(target=inference_loop, args=(result, result_lock))
    picture_thread.start()


def execute_avoid_sequence(params=avoid_actions_params, sequence=avoid_actions_sequence):
    logging.info("进入 execute_avoid_sequence")
    logging.info("--------params--------: %s", params)
    # 遍历避障动作序列
    for action_id, params_index in sequence:
        # 根据动作ID获取对应的动作函数
        action_func = actions_dict.get(action_id, None)
        if action_func:
            # 获取避障参数
            avoid_params = params[action_id][params_index]
            # 如果参数是元组类型，则创建并启动避障动作线程
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


def main_loop(sfd, target_address):
    # 定义全局变量和局部变量
    global continue_loop, sequence_index, actions_params, actions_sequence
    while continue_loop:
        continue_loop = False  # 重置循环控制变量
        # 遍历动作序列
        for action_id, params_index in actions_sequence:
            # 根据动作ID获取对应的动作函数
            action_func = actions_dict.get(action_id, None)
            if action_func:
                # 获取动作参数
                params = actions_params[action_id][params_index]
                # 打印当前参数
                logging.info(f'params: {params}')
                # 如果参数是元组类型，则创建线程执行动作
                if isinstance(params, tuple):
                    thread = action_func(*params)
                    thread.start()   # 启动线程
                    # 等待线程执行完毕
                    while thread.is_alive():
                        # 使用上下文管理器确保线程安全地访问状态列表和结果列表
                        with ExitStack() as stack:
                            stack.enter_context(status_list_lock)
                            stack.enter_context(result_lock)
                            # 处理避障、楼梯、坑洞和状态
                            handle_obstacles(thread, params)
                            handle_staircases(sfd, target_address)
                            handle_holes(sfd, target_address)
                    # 如果循环控制变量被设置为False，则退出循环
                    if not continue_loop:
                        # 增加队列角标
                        sequence_index += 1  # 成功走完一个，队列角标加一
                        thread.join()
                        handle_status(sfd, target_address)
                    # 如果循环控制变量被设置为True，则跳出当前循环
                    if continue_loop:
                        break
                time.sleep(1)


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


def handle_staircases(sfd, target_address):
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


def handle_holes(sfd, target_address):
    # 定义全局变量
    global hole
    # 如果未遇到狗洞，并且结果列表为['hole'], 表示检测到狗洞
    if hole == 0 and result == ['hole']:
        # 增加狗洞计数
        hole += 1
        # 打印检测到狗洞的信息
        logging.info("Detected 'hole', pausing thread.")
        # 发送指令以暂停机械狗
        SendToCommand.perform_action(sfd, target_address, 0x21010406, 0, 0)


def handle_status(sfd, target_address):
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


if __name__ == "__main__":
    # 建立通讯地址
    sfd, target_address = initialize_communication()
    # 初始化模型、雷达、识别
    initialize_threads()
    # 站立
    SendToCommand.perform_action(sfd, target_address, 0x21010202, 0, 0)
    # 2秒延时保证机器狗站稳再开始执行任务
    time.sleep(2)
    # 进入主程序
    main_loop(sfd, target_address)
