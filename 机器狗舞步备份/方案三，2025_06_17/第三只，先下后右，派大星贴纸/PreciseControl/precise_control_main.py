#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import logging
from pprint import pprint

# 导入定义的机械狗相关的包
from threading_utils.ThreadTemplates import *           # 线程的模板与基本轴指令的发送
from sendcommand import SendToCommand, heartbeat        # 发送简单指令与心跳包
from socketnetwork import network_utils                 # 通信函数
from command.udp_command import *                       # 存放各种结构体与状态数据、指令
from speeds.sportspeed import *                         # 运动精准控制的基础版模型

# 初始化日志，级别为最低级
logging.basicConfig(level=logging.DEBUG)

# 建立通讯
sfd, target_address = network_utils.setup_socket_and_address()

# 定义发送心跳包的线程执行体
# 注意*args必须以tuple形式传入，包括sfd和target_address
heartbeat_thread = MyRepeatThread("HeartbeatThread", heartbeat.send_udp_heartbeat, 0.25, None, sfd, target_address)
heartbeat_thread.start()


action_CommandHead = CommandHead()


# 调用机器狗动作,将机械狗的值传入进结构体中
action_CommandHead.code = dog_actions.get("ACTION_STAND_DOWN")
SendToCommand.perform_action(sfd, target_address, action_CommandHead.code, 0, 0)
time.sleep(2)


SendToCommand.perform_action(sfd, target_address, 0x21010C02, 0, 0)

# hight_walk
# SendToCommand.perform_action(sfd, target_address, 0x21010407, 0, 0)

time.sleep(2)


actions_name = {
    1: '直走（0.3表示前进0.3米，-0.3表示后退0.3米）',
    2: '平移（0.3表示右平移0.3米，-0.3表示左平移0.3米）',
    3: '旋转（45表示向右旋转45度，-45表示向做旋转45度）',
    4: '扭身体',
    5: '打招呼',
}

actions_params = {}
actions_sequence = []
val1, val2, val3, val4, val5 = [], [], [], [], []

print("下面即将进入到输入环节，根据你输入的数字和参数索引，机械狗将会做出相应运动")
print("输入格式：动作ID,参数索引，例如：3,2,1,2,3,1（依次用英文逗号分隔开）")

x = input("请输入动作ID(回车结束)：")
x = x.split(',')
x = [i for i in x if i != '']
for action_id in x:

    actions_sequence.append((int(action_id), 0))  # 假设总是使用参数列表中的第一个参数
def update_actions_sequence(actions_sequence):
    # 初始化计数器
    count_1 = 0
    count_2 = 0
    count_3 = 0
    count_4 = 0
    count_5 = 0

    # 结果列表
    updated_sequence = []

    # 遍历原始序列
    for action in actions_sequence:
        if action[0] == 3:
            # 如果是3，更新3的计数器
            updated_sequence.append((3, count_3))
            count_3 += 1
        elif action[0] == 1:
            # 如果是1，更新1的计数器
            updated_sequence.append((1, count_1))
            count_1 += 1
        elif action[0] == 2:
            # 如果是2，更新2的计数器
            updated_sequence.append((2, count_2))
            count_2 += 1
        elif action[0] == 4:
            updated_sequence.append((4, count_4))
            count_4 += 1
        elif action[0] == 5:
            updated_sequence.append((5, count_5))
            count_5 += 1
    return updated_sequence

actions_sequence = update_actions_sequence(actions_sequence)

logging.info('这里可以设置速度挡位，比如在显示前进的时候可以出入  0.3,6   意思是以6档的速度前进0.3米')

for index, action in enumerate(actions_sequence):
    action_name = actions_name.get(action[0], "未知动作")
    print(f'第{index+1}个动作是：{action_name}')
    vals = input('你想要做的操作是：')

    # 检查是否包含逗号
    if ',' in vals:
        # 如果包含逗号，则将输入按逗号分割
        vals = vals.split(',')
        # 转换每个分割项为浮点数
        vals = tuple(float(val.strip()) for val in vals)
    else:
        # 如果没有逗号，则直接转换为浮点数
        vals = (float(vals),)

    print(vals)

    if action[0] == 1:
        val1.append(vals,)
    elif action[0] == 2:
        val2.append(vals,)
    elif action[0] == 3:
        val3.append(vals,)
    elif action[0] == 4:
        val4.append(vals,)
    elif action[0] == 5:
        val5.append(vals,)

actions_params = {
    1: val1,
    2: val2,
    3: val3,
    4: val4,
    5: val5,
}

print(actions_params)
       

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
        




