import cv2
from cvzone.HandTrackingModule import HandDetector
import math
import numpy as np
import cvzone
import sys
sys.path.append("..")

from HKcamera import getImage

from ridge_np import *

# cap = cv2.VideoCapture('rtsp://192.168.1.120:8554/test')
# cap.set(3, 640)  # 设置帧的宽度
# cap.set(4, 480)  # 设置帧的高度

# 实例化手部检测器，此处仅初始化了检测器，并没有在代码后面使用它
detector = HandDetector(detectionCon=0.8, maxHands=2)

# 初始化视频保存器
# fourcc = cv2.VideoWriter_fourcc(*'XVID')  # 设置视频编解码器
# out = cv2.VideoWriter('output.avi', fourcc, 4.0, (640, 480))  # 创建VideoWriter对象

while True:
    # success, img = cap.read()
    # image_bgr = getImage()
    # img = image_bgr.copy()
    img = getImage()
    # if image_bgr:  # 检查帧是否成功读取
    # 这个的 draw = False 是指只显示实际距离的检测框，手部的检测框不显示
    hands, img = detector.findHands(img, draw=False)
    list0 = []
    if hands:
        lmList = hands[0]['lmList']

        # print(hands[0]['type'])
        # print(hands[0]['center'])
        x,y,w,h = hands[0]['bbox']
        # if 1<x+w<639 and 19< x+h <479:
        x1, y1, z1 = lmList[5]
        x2, y2, z2 = lmList[17]
        x3, y3, z3 = lmList[0]
        x4, y4, z4 = lmList[12]

        angle_xy = predict_angle(hands[0]['center'][0], hands[0]['center'][1])
        distanceCM = predict_distance(x1, x2, x3, x4, y1, y2, y3, y4)
        angle = angle_xy[0]
        print("距离：", distanceCM)
        print("角度", angle)
        # image_draw = cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 255), 3)

        # cvzone.putTextRect(img, f'{int(distanceCM)} CM', (x + 5, y - 60))
        # cvzone.putTextRect(img, f'{int(angle)} du', (x + 5, y - 10))

        # cv2.imshow("Image", image_draw)
        # out.write(image_draw)  # 将帧写入视频文件

    # 按 'q' 键退出循环
    # if cv2.waitKey(1) & 0xFF == ord('q'):
    #     break



