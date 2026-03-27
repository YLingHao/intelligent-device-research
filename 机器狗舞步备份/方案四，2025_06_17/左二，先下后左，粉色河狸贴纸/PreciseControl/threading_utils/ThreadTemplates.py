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
        self.start_time = time.time()  # 记录线程开始的时间
        self.global_var = 0   
        self.current_time = time.time() # 当前时间
        self.current_time_start = 0

        
    def run(self) -> None:
        print(f"Starting {self.name}")
        while not self.stopped.is_set():
            self.current_time = time.time()
            
            # 如果超过时间阈值，则停止线程
            if self.time_limit is not None and self.check_time_and_stop(time.time()):
                break

            try:
                self.action(*self.args)  # 展开参数
            except KeyboardInterrupt:
                self.stopped = True
            finally:
                pass

            # 计算需要休眠多长时间以保持固定频率
            action_start_time = time.time()
            elapsed_time = action_start_time - self.current_time
            time_to_wait = max(0, self.interval - elapsed_time)
            time.sleep(time_to_wait)

        self.stopped.set()  # 确保线程停止状态被设置
        logging.info(f'离开线程：{self.name}')

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

    def print_attributes(self):
        """
        打印对象的所有属性及其值
        """
        self.current_time_start = time.time() - self.start_time
        return {attr: value for attr, value in vars(self).items()}


def action_go_straight(long, speedgear=3) -> MyRepeatThread:
    # 计算前进命令,long=0.3代表前进30厘米
    times, val = go_straight(long, speedgear)
    ACTION_pan_back_and_forth_thread = MyRepeatThread("ACTION_pan_back_and_forth_thread", SendToCommand.perform_action, 0.1, times, sfd, target_address, 0x21010130, val, 0)
    # ACTION_pan_back_and_forth_thread.start()
    return ACTION_pan_back_and_forth_thread

def action_turn_left_and_right(long, speedgear=3) -> MyRepeatThread:
    # 计算平移命令,long=0.3代表右平移30厘米
    times, val = translate_left_and_right(long, speedgear)
    ACTION_turn_left_and_right_thread = MyRepeatThread("ACTION_turn_left_and_right_thread", SendToCommand.perform_action, 0.1, times, sfd, target_address, 0x21010131, val, 0)
    # ACTION_turn_left_and_right_thread.start()
    return ACTION_turn_left_and_right_thread

def action_revolve_left_and_right(angle, add_timer = 0) -> MyRepeatThread:
    # 计算旋转命令,angle=30.3代表右旋转30度
    times, val = revolve_left_and_right(angle)
    ACTION_revolve_left_and_right = MyRepeatThread("ACTION_revolve_left_and_right", SendToCommand.perform_action, 0.1, times + add_timer, sfd, target_address, 0x21010135, val, 0)
    # ACTION_revolve_left_and_right.start()
    return ACTION_revolve_left_and_right

def action_twist_body(times) -> MyRepeatThread:
    # 执行扭身体命令
    ACTION_action_twist_body = MyRepeatThread("ACTION_action_twist_body", SendToCommand.perform_action, 0.1, times, sfd, target_address, 0x21010204, 0, 0)
    return ACTION_action_twist_body
    
def action_greet(times) -> MyRepeatThread:
    # 执行打招呼命令
    ACTION_greet = MyRepeatThread("ACTION_greet", SendToCommand.perform_action, 0.1, times, sfd, target_address, 0x21010507, 0, 0)
    return ACTION_greet
    
def action_adjust_the_pitch_angle(angle, timer) -> MyRepeatThread:
    # 执行调整仰俯角命令
    ACTION_adjust_the_pitch_angle = MyRepeatThread("ACTION_adjust_the_pitch_angle", SendToCommand.perform_action, 0.1, timer, sfd, target_address, 0x21010130, angle, 0)
    return ACTION_adjust_the_pitch_angle

def action_adjust_the_roll_angle(angle, timer) -> MyRepeatThread:
    # 执行调整横滚角命令
    ACTION_adjust_the_roll_angle = MyRepeatThread("ACTION_adjust_the_roll_angle", SendToCommand.perform_action, 0.1, timer, sfd, target_address, 0x21010131, angle, 0)
    return ACTION_adjust_the_roll_angle
    
def action_adjust_the_height_of_body(angle, timer) -> MyRepeatThread:
    # 执行调整身体高度命令
    ACTION_adjust_the_height_of_body = MyRepeatThread("ACTION_adjustthe_height_of_body", SendToCommand.perform_action, 0.1, timer, sfd, target_address, 0x21010102, angle, 0)
    return ACTION_adjust_the_height_of_body
    
def action_adjust_the_yaw_angle(angle, timer) -> MyRepeatThread:
    # 执行调整偏航角命令
    ACTION_adjust_the_yaw_angle = MyRepeatThread("ACTION_adjust_the_yaw_angle", SendToCommand.perform_action, 0.1, timer, sfd, target_address, 0x21010135, angle, 0)
    return ACTION_adjust_the_yaw_angle
    
def action_stand_down(timer = 1.5) -> MyRepeatThread:
    # 执行起立或趴下命令
    ACTION_stand_down = MyRepeatThread("ACTION_stand_down", SendToCommand.perform_action, 0.1, timer, sfd, target_address, 0x21010202, 0, 0)
    return ACTION_stand_down

def action_twist_jump(type_) -> MyRepeatThread:
    # 执行扭身跳命令
    ACTION_twist_jump = MyRepeatThread("ACTION_twist_jump", SendToCommand.perform_action, 0.1, 2.25, sfd, target_address, 0x2101020D, 0, 0)
    return ACTION_twist_jump

def action_jump_forward(type_) -> MyRepeatThread:
    # 执行向前跳命令
    ACTION_jump_forward = MyRepeatThread("ACTION_jump_forward", SendToCommand.perform_action, 0.1, 2.25, sfd, target_address, 0x2101050B, 0, 0)
    return ACTION_jump_forward

def action_continuous_exercise_start(timer) -> MyRepeatThread:
    # 执行持续运动命令
    ACTION_continuous_exercise_start = MyRepeatThread("ACTION_continuous_exercise_start", SendToCommand.perform_action, 0.1, timer, sfd, target_address, 0x21010C06, -1, 0)
    return ACTION_continuous_exercise_start
def action_continuous_exercise_stop(timer) -> MyRepeatThread:
    # 停止持续运动命令
    ACTION_continuous_exercise_stop = MyRepeatThread("ACTION_continuous_exercise_stop", SendToCommand.perform_action, 0.1, 0.1, sfd, target_address, 0x21010C06, 2, 0)
    return ACTION_continuous_exercise_stop

def action_in_place_mode(timer) -> MyRepeatThread:
    # 变更为原地模式
    ACTION_in_place_mode = MyRepeatThread("ACTION_in_place_mode", SendToCommand.perform_action, 0.1, timer, sfd, target_address, 0x21010D05, 0, 0)
    return ACTION_in_place_mode
    
def action_mobile_mode(timer) -> MyRepeatThread:
    # 变更为移动模式
    ACTION_mobile_mode = MyRepeatThread("ACTION_mobile_mode", SendToCommand.perform_action, 0.1, timer, sfd, target_address, 0x21010D06, 0, 0)
    return ACTION_mobile_mode
    
def action_moonwalk(times) -> MyRepeatThread:
    # 执行太空步命令
    ACTION_moonwalk = MyRepeatThread("ACTION_moonwalk", SendToCommand.perform_action, 0.1, times, sfd, target_address, 0x2101030C, 0, 0)
    return ACTION_moonwalk
    
def action_flatland_slow_walk(timer) -> MyRepeatThread:
    # 平地低速步态
    ACTION_flatland_slow_walk = MyRepeatThread("ACTION_flatland_slow_walk", SendToCommand.perform_action, 0.1, timer, sfd, target_address, 0x21010300, 0, 0)
    return ACTION_flatland_slow_walk
    
def action_flatland_medium_walk(timer) -> MyRepeatThread:
    # 平地中速步态
    ACTION_flatland_medium_walk = MyRepeatThread("ACTION_flatland_medium_walk", SendToCommand.perform_action, 0.1, timer, sfd, target_address, 0x21010307, 0, 0)
    return ACTION_flatland_medium_walk

def action_flatland_fast_walk(timer) -> MyRepeatThread:
    # 平地高速步态
    ACTION_flatland_fast_walk = MyRepeatThread("ACTION_flatland_fast_walk", SendToCommand.perform_action, 0.1, timer, sfd, target_address, 0x21010303, 0, 0)
    return ACTION_flatland_fast_walk
    
def action_normal_crawl(timer) -> MyRepeatThread:
    # 切换正常/匍匐态
    ACTION_normal_crawl = MyRepeatThread("ACTION_normal_crawl", SendToCommand.perform_action, timer, timer, sfd, target_address, 0x21010406, 0, 0)
    return ACTION_normal_crawl
    
def action_grasping_obstacle_walk(timer) -> MyRepeatThread:
    # 切换成抓地越障步态
    ACTION_grasping_obstacle_walk = MyRepeatThread("ACTION_grasping_obstacle_walk", SendToCommand.perform_action, 0.1, timer, sfd, target_address, 0x21010402, 0, 0)
    return ACTION_grasping_obstacle_walk
    
def action_general_obstacle_walk(timer) -> MyRepeatThread:
    # 切换成通用越障步态
    ACTION_general_obstacle_walk = MyRepeatThread("ACTION_general_obstacle_walk", SendToCommand.perform_action, 0.1, timer, sfd, target_address, 0x21010401, 0, 0)
    return ACTION_general_obstacle_walk
    
def action_high_step_obstacle_walk(timer) -> MyRepeatThread:
    # 切换成高踏步越障步态
    ACTION_high_step_obstacle_walk = MyRepeatThread("ACTION_high_step_obstacle_walk", SendToCommand.perform_action, 0.1, timer, sfd, target_address, 0x21010407, 0, 0)
    return ACTION_high_step_obstacle_walk
    
actions_dict = {
    0: action_stand_down, #起立或趴下
    1: action_go_straight, #前进或后退
    2: action_turn_left_and_right, #左走或右走
    3: action_revolve_left_and_right, #旋转
    4: action_twist_body, #扭身体
    5: action_greet, #打招呼
    6: action_moonwalk, #太空步
    7: action_twist_jump, #扭身跳
    8: action_continuous_exercise_start, #开始持续运动模式
    9: action_continuous_exercise_stop, #停止持续运动模式
    10: action_jump_forward, #向前跳
    11: action_adjust_the_roll_angle, #调整横滚角
    12: action_adjust_the_pitch_angle, #调整俯仰角
    13: action_adjust_the_height_of_body, #调整身体高度
    14: action_adjust_the_yaw_angle,  #调整偏航角
    21: action_flatland_slow_walk, #平地低速步态
    22: action_flatland_medium_walk, #平地中速步态
    23: action_flatland_fast_walk,  #平地高速步态
    31: action_normal_crawl, #切换正常态和匍匐态
    32: action_grasping_obstacle_walk, #切换成抓地越障步态
    33: action_general_obstacle_walk, #切换成通用越障步态
    34: action_high_step_obstacle_walk, #切换成高踏步越障步态
    98: action_mobile_mode, #移动模式
    99: action_in_place_mode, #原地模式
    # 其他函数根据实际情况添加
}






