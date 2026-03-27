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
action_list = [[9, [1]], [99, [1]],
              # ǰ15��
              [14, [35000, 1]], [14, [-35000, 1]], [14, [35000, 1]], [14, [-35000, 1]], [14, [0, 0.5]],
              [8, [2.8]], [3, [45]], [3, [-90]], [3, [90]], [3, [-90]], [3, [45, -0.125]], [98, [1]], [8, [1]], [9, [1]],
              # 15�뵽40�벿��
              [10, [2.25]],  [8, [1]], [9, [1]], [5, [7]], [1, [-1.2]], [8, [1]], [9, [1]], [98, [1]],
              # 40���
              [3, [-45]], [8, [1]], [23, [1]], [1, [1, 6]], [9, [1]], [5, [7]], [8, [3]], [23, [1]], [1, [-1, 6]], [21, [1]], 
              [3, [90]], [8, [1]], [23, [1]], [1, [1, 6]], [9, [1]], [5, [7]], [8, [3]], [23, [1]], [1, [-1, 6]], [21, [1]],
              [3, [-45]], [9, [1]], [8, [2]],
              # 1��20���
              [3, [90]], [1, [3]], [3, [-90]], [1, [3]], [8, [1]]]

              #[0, [0]]]

for action_data in action_list:
    action_func = actions_dict.get(action_data[0], None)
    if action_func:
        params = action_data[1]
        thread = action_func(*params)
        thread.start()
        thread.join()