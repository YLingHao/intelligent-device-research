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
#SendToCommand.perform_action(sfd, target_address, action_CommandHead.code, 0, 0)
#time.sleep(2)

#SendToCommand.perform_action(sfd, target_address, 0x21010C02, 0, 0)
time.sleep(1)

# xi1aum
# 横向6档，2.2 = 2
action_list = [[2, [2.35, 6]]]

              #[0, [0]]]

for action_data in action_list:
    action_func = actions_dict.get(action_data[0], None)
    if action_func:
        params = action_data[1]
        thread = action_func(*params)
        thread.start()
        thread.join()