
import math

import cv2
from cvzone.HandTrackingModule import HandDetector
import numpy as np
import cvzone
import pandas as pd
import os

file_name = 'test.csv'


# 设置CSV文件的列名
columns = ['real_distance', '5-17', '0-12']

# 创建空的DataFrame
data = pd.DataFrame(columns=columns)

# 检查文件是否存在且包含正确的列头
if not os.path.isfile(file_name) or os.path.getsize(file_name) == 0:
    data.to_csv(file_name, index=False)  # 第一次或文件不存在，写入列头
else:
    data.to_csv(file_name, mode='a', index=False, header=False)  # 追加数据，不包括列头
# 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90, 95, 100, 105, 110, 120, 130, 140, 150, 200
real_distance = 20
# Hand_direction = 1


cap = cv2.VideoCapture(0)
cap.set(3, 640)  # 设置帧的宽度
cap.set(4, 480)  # 设置帧的高度


# 实例化手部检测器，此处仅初始化了检测器，并没有在代码后面使用它
detector = HandDetector(detectionCon=0.8, maxHands=2)

while True:
    success, img = cap.read()

    if success:  # 检查帧是否成功读取
        # 这个的 draw = False 是指只显示实际距离的检测框，手部的检测框不显示
        hands, img = detector.findHands(img)
        if hands:
            lmList = hands[0]['lmList']
            # hand_type=['Left', 'Right']
            # if hand_type[Hand_direction] == hands[0]['type']:
            hand_data = []
            x, y, w, h = hands[0]['bbox']
            x1, y1, z1 = lmList[5]
            x2, y2, z2 = lmList[17]
            x3, y3, z3 = lmList[0]
            x4, y4, z4 = lmList[12]
            distance1 = int(math.sqrt((y2 - y1) ** 2 + (x2 - x1) ** 2))
            distance2 = int(math.sqrt((y4 - y3) ** 2 + (x4 - x3) ** 2))
            hand_data += [real_distance, distance1, distance2]

            # 添加当前手部数据到DataFrame
            data_length = len(data)
            data.loc[data_length] = hand_data


        cv2.imshow("Image", img)

    # 按 'q' 键退出循环
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

# 在捕获循环结束后，通过指定mode='a'和header=False来追加数据
data.to_csv(file_name, mode='a', index=False, header=False)