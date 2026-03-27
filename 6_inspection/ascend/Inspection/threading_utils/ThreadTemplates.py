#!/usr/bin/env python
# -*- coding: utf-8 -*-

import threading
import time
import logging

from speeds.sportspeed import *
from sendcommand import SendToCommand, heartbeat
from socketnetwork import network_utils

# 配置日志
logging.basicConfig(level=logging.DEBUG)

sfd, target_address = network_utils.setup_socket_and_address()

class MyRepeatThread(threading.Thread):
    def __init__(self, name, action, interval, time_limit = None, *args) -> None:
        super(MyRepeatThread, self).__init__()
        self.name = name
        self.action = action
        self.interval = interval  # 发送命令的频率
        self.time_limit = time_limit  # 最大时间阈值
        self.args = args
        self.stopped = threading.Event()
        self.start_time = time.monotonic()  # 记录线程开始的时间
        self.global_var = 0   
        self.current_time = time.monotonic()  # 当前时间
        self.current_time_start = 0

        
    def run(self) -> None:
        logging.info(f"Starting {self.name}")
        try:
            while not self.stopped.is_set():
                self.current_time = time.monotonic()
                
                # 如果超过时间阈值，则停止线程
                if self.time_limit is not None and self.check_time_and_stop(self.current_time):
                    break

                try:
                    self.action(*self.args)  # 展开参数
                except KeyboardInterrupt:
                    self.stopped = True
                finally:
                    pass

                # 计算需要休眠多长时间以保持固定频率
                action_start_time = time.monotonic()
                elapsed_time = action_start_time - self.current_time
                time_to_wait = max(0, self.interval - elapsed_time)
                time.sleep(time_to_wait)
        finally:
            self.stopped.set()  # 确保线程停止状态被设置
            logging.info(f"Exiting thread: {self.name}")


    def check_time_and_stop(self, current_time) -> bool:
        if current_time - self.start_time > self.time_limit:
            logging.info(f'{self.name}由于超过时间阈值{self.time_limit}秒，系统自动停止！')
            self.stopped.set()
            return True
        elif self.global_var == 1:
            self.stopped.set()
            return True
        return False
    

    def stop(self) -> None:
        self.stopped.set()

    def print_attributes(self)-> dict:
        """
        打印对象的所有属性及其值
        """
        self.current_time_start = time.monotonic() - self.start_time
        return {attr: value for attr, value in vars(self).items()}



def action_go_straight(long, speedgear=3) -> MyRepeatThread:
    # 计算前进命令,long=0.3代表前进30厘米
    times, val = go_straight(long, speedgear)
    ACTION_pan_back_and_forth_thread = MyRepeatThread("ACTION_pan_back_and_forth_thread", SendToCommand.perform_action, 
                                                      0.1, times, sfd, target_address, 0x21010130, val, 0)
    # ACTION_pan_back_and_forth_thread.start()
    return ACTION_pan_back_and_forth_thread


def action_turn_left_and_right(long, speedgear=3) -> MyRepeatThread:
    # 计算平移命令,long=0.3代表右平移30厘米
    times, val = translate_left_and_right(long, speedgear)
    ACTION_turn_left_and_right_thread = MyRepeatThread("ACTION_turn_left_and_right_thread", SendToCommand.perform_action,
                        0.1, times, sfd, target_address, 0x21010131, val, 0)
    # ACTION_turn_left_and_right_thread.start()
    return ACTION_turn_left_and_right_thread


def action_revolve_left_and_right(angle) -> MyRepeatThread:
    # 计算旋转命令,angle=30.3代表右旋转30度
    times, val = revolve_left_and_right(angle)
    ACTION_revolve_left_and_right = MyRepeatThread("ACTION_revolve_left_and_right", SendToCommand.perform_action,
                            0.1, times, sfd, target_address, 0x21010135, val, 0)
    # ACTION_revolve_left_and_right.start()
    return ACTION_revolve_left_and_right


actions_dict = {
    1: action_go_straight,
    2: action_turn_left_and_right,
    3: action_revolve_left_and_right,
    # 其他函数根据实际情况添加
}

def action_the_pitch_angle():
    ACTION_Adjust_the_pitch_angle = MyRepeatThread("ACTION_Adjust_the_pitch_angle", SendToCommand.perform_action,
                            0.1, 20, sfd, target_address, 0x21010130, 15000, 0)
    # ACTION_revolve_left_and_right.start()
    return ACTION_revolve_left_and_right





