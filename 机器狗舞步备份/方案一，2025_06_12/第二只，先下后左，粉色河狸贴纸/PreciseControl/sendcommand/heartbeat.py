#!/usr/bin/env python
# -*- coding: utf-8 -*-

import socket
import struct
import time

def send_udp_heartbeat(sfd, target_address, code=0x21040001, parameters_size=0, type=0, heartbeat_interval=0.25) -> None:
    # 打包心跳指令数据
    heartbeat_command = struct.pack('<III', code, parameters_size, type)

    try:
        while True:
            # 记录发送前的时间
            start_time = time.time()

            # 发送心跳包
            sfd.sendto(heartbeat_command, target_address)

            # 发送后的延时
            time.sleep(max(0, heartbeat_interval - (time.time() - start_time)))

    except KeyboardInterrupt:
        print("Heartbeat sending stopped by user.")
    finally:
        # 关闭socket
        sfd.close()
