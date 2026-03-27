#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import logging
from pprint import pprint

# ���붨��Ļ�е����صİ�
from threading_utils.ThreadTemplates import *           # �̵߳�ģ���������ָ��ķ���
from sendcommand import SendToCommand, heartbeat        # ���ͼ�ָ����������
from socketnetwork import network_utils                 # ͨ�ź���
from command.udp_command import *                       # ��Ÿ��ֽṹ����״̬���ݡ�ָ��
from speeds.sportspeed import *                         # �˶���׼���ƵĻ�����ģ��

# ��ʼ����־������Ϊ��ͼ�
logging.basicConfig(level=logging.DEBUG)

# ����ͨѶ
sfd, target_address = network_utils.setup_socket_and_address()

# ���巢�����������߳�ִ����
# ע��*args������tuple��ʽ���룬����sfd��target_address
heartbeat_thread = MyRepeatThread("HeartbeatThread", heartbeat.send_udp_heartbeat, 0.25, None, sfd, target_address)
heartbeat_thread.start()


action_CommandHead = CommandHead()


# ���û���������,����е����ֵ������ṹ����
action_CommandHead.code = dog_actions.get("ACTION_STAND_DOWN")
#SendToCommand.perform_action(sfd, target_address, action_CommandHead.code, 0, 0)
#time.sleep(2)

#SendToCommand.perform_action(sfd, target_address, 0x21010C02, 0, 0)
#time.sleep(1)

# xi1aum
# ����6����2.2 = 2
action_list = [
              [9, [1]], 
              # 前跳
              [10, [2.25]], [8, [1]], [9, [1]], [-1, [1]], 
              # 高速往右走
              [23, [1]], [2, [0.5, 6]], [21, [1]],
              
              [8, [1]]
              ]

              #[0, [0]]]

for action_data in action_list:
    action_func = actions_dict.get(action_data[0], None)
    if action_func:
        params = action_data[1]
        thread = action_func(*params)
        thread.start()
        thread.join()