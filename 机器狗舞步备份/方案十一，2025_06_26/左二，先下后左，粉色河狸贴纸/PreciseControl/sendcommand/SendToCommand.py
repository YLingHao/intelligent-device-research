#!/usr/bin/env python
# -*- coding: utf-8 -*-

import socket
import struct
import ctypes
from ctypes import c_double, c_uint8, c_int32
from command.udp_command import *                       # 存放各种结构体与状态数据、指令


def send_command(sfd, target_address, code, parameters_size, type_) -> None:
    # 注意：在 Python 中，'type' 是预留关键字，这里我们使用 'type_'
    command_head = struct.pack('<3i', code, parameters_size, type_)
    # 发送命令头部到目标地址，这里确保只发送一次s
    bytes_sent = sfd.sendto(command_head, target_address)
    # print(f"Bytes sent: {bytes_sent}")

def perform_action(sfd, target_address, code, parameters_size, type_) -> None:
    # 使用默认的 parameters_size 和 type 的值是 0
    send_command(sfd, target_address, code, parameters_size, type_)




# def sendto_command(sfd, target_address, cm):

#     # 发送

#     # 获取命令头部的打包格式
#     command_head_format = 'iii'

#     # 将命令头部打包
#     command_head_packed = struct.pack(command_head_format, cm.command.code, cm.command.paramters_size, cm.command.type_)
    
#     # 获取RobotState实例的字节表示
#     command_data_packed = ctypes.string_at(ctypes.byref(cm.data_buffer), ctypes.sizeof(cm.data_buffer))
    
#     # 整个命令的打包数据 = 命令头部 + RobotState数据
#     packed_command = command_head_packed + command_data_packed
    
#     # 发送打包好的数据
#     bytes_sent = sfd.sendto(packed_command, target_address)
#     # print("bytes_sent", bytes_sent)
#     return bytes_sent

def sendto_command(sfd, target_address, cm):
    # Pack the command head into binary data
    head_data = struct.pack('III', cm.head.code, cm.head.parameters_size, cm.head.type_)
    
    # Pack the command data into binary data
    data_data = struct.pack('{}I'.format(Command.kDataSize), *cm.data)
    
    # Calculate the total size of the command
    total_size = struct.calcsize('III') + len(data_data)
    
    # Send the command to the target address
    # Note: You need to implement the sending logic
    # sendto(sfd, head_data + data_data, target_address)
    print("Sending command to target address:", target_address)
    print("Command head:", head_data)
    print("Command data:", data_data)
    print("Total size:", total_size)

