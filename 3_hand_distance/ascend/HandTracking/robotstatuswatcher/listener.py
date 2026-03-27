#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
sys.path.append('../')

from command.udp_command import *
from socketnetwork import network_utils

sock_fd = network_utils.set_up_recvfrom_socket_and_address()

def status_listener_radar(status_list, status_list_lock):
    while True:
        recv_data, _ = sock_fd.recvfrom(1024)  # 假设接收的数据不会超过1024字节
        recv_num = len(recv_data)
        # print(recv_num)
        if recv_num == 108:  # 确保接收到的数据长度正确
            dr = JointStateReceived(recv_data)
            if dr.code == 2306:  # 2306是0x0902关机角度的指令码
                joint_angle = JointAngle(dr)  # 通过code判断，在JointAngle中访问特定JointStateReceived的实例data属性
                # print("code: ", dr.code)
                # print("解析后")
                # print("Received Joint Angles:", joint_angle.joint_angles)
                
            if dr.code == 2307:  # 2307是0x0903关节角速度的指令码
                joint_speed = JointSpeed(dr)
                # print("code: ", dr.code)
                # print("解析后")
                # print("Received Joint Speed:", joint_speed.joint_speeds)

        elif recv_num == 212:
            dr, status_list_temp = RobotState(recv_data), []
            if dr.code == 2305:   # 机器状态数据
                if dr.robot_basic_state != 0:
                    # print("机器人基本运动状态:",dr.robot_basic_state)
                    # print("机器人步态信息:",dr.robot_gait_state)
                    # print("机器人动作状态:",dr.robot_motion_state)    
                    status_list_temp.append(dr.robot_basic_state)
                    status_list_temp.append(dr.robot_gait_state)
                    status_list_temp.append(dr.robot_motion_state)
                    status_list_temp.append(dr.distance_ahead)
                    # status_list_temp.append(dr.rear_distance)
                    # print('status_list', status_list_temp)
                    # print(status_list_temp[3])

                    with status_list_lock:
                        status_list[:] = status_list_temp  # 更新全局的status_list
            
def status_listener():
    while True:
        recv_data, _ = sock_fd.recvfrom(1024)  # 假设接收的数据不会超过1024字节
        recv_num = len(recv_data)
        # print(recv_num)
        if recv_num == 108:  # 确保接收到的数据长度正确
            dr = JointStateReceived(recv_data)
            if dr.code == 2306:  # 2306是0x0902关机角度的指令码
                joint_angle = JointAngle(dr)  # 通过code判断，在JointAngle中访问特定JointStateReceived的实例data属性
                # print("code: ", dr.code)
                # print("解析后")
                # print("Received Joint Angles:", joint_angle.joint_angles)
                
            if dr.code == 2307:  # 2307是0x0903关节角速度的指令码
                joint_speed = JointSpeed(dr)
                # print("code: ", dr.code)
                # print("解析后")
                # print("Received Joint Speed:", joint_speed.joint_speeds)

        elif recv_num == 212:
            dr, status_list_temp = RobotState(recv_data), []
            if dr.code == 2305:   # 机器状态数据
                if dr.robot_basic_state != 0:
                    # print("机器人基本运动状态:",dr.robot_basic_state)
                    # print("机器人步态信息:",dr.robot_gait_state)
                    # print("机器人动作状态:",dr.robot_motion_state)    
                    status_list_temp.append(dr.robot_basic_state)
                    status_list_temp.append(dr.robot_gait_state)
                    status_list_temp.append(dr.robot_motion_state)
                    return status_list_temp
              