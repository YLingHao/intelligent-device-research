i#!/bin/bash
ip link set can0 down
ip link set can1 down
ip link set can2 down

ip link set can0 up type can bitrate 1000000
ip link set can1 up type can bitrate 1000000
ip link set can2 up type can bitrate 1000000
cansend can0 001#FFFFFFFFFFFFFFFD
cansend can0 002#FFFFFFFFFFFFFFFD
cansend can0 003#FFFFFFFFFFFFFFFD
cansend can0 004#FFFFFFFFFFFFFFFD
cansend can1 002#FFFFFFFFFFFFFFFD
cansend can1 003#FFFFFFFFFFFFFFFD
cansend can1 004#FFFFFFFFFFFFFFFD
cansend can1 005#FFFFFFFFFFFFFFFD
cansend can2 001#FFFFFFFFFFFFFFFD
cansend can2 002#FFFFFFFFFFFFFFFD
cansend can2 003#FFFFFFFFFFFFFFFD
cansend can2 004#FFFFFFFFFFFFFFFD

