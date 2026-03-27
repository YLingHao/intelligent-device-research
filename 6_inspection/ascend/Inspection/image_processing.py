#!/usr/bin/env python
# -*- coding: utf-8 -*-

import cv2
import numpy as np
import math



# 调整圆的参数
canny_threshold1 = 55  # Canny 边缘检测的低阈值-圆
canny_threshold2 = 180  # Canny 边缘检测的高阈值-圆
gaussian_blur_ksize = (9, 9)  # 高斯模糊的核大小-圆
gaussian_blur_sigmaX = 3  # 高斯模糊的标准差-圆
hough_dp = 1.2  # 霍夫变换中的反比例系数-圆
hough_minDist = 100  # 霍夫变换中检测到的圆的最小距离-圆
hough_param1 = 100  # 霍夫变换的第一个参数（Canny 边缘检测的高阈值） -圆
hough_param2 = 30  # 霍夫变换的第二个参数（累加器阈值）-圆
hough_minRadius = 20  # 检测圆的最小半径
hough_maxRadius = 150  # 检测圆的最大半径
inner_circle_scale = 0.75  # 内部检测区域的缩放系数，例如0.75表示内部区域半径为圆形半径的75%

# 调整直线的参数
canny_threshold3 = 55  # Canny 边缘检测的低阈值-直线
canny_threshold4 = 130  # Canny 边缘检测的高阈值-直线
gaussian_blur_ksize_line = (9, 9)  # 高斯模糊的核大小-直线
gaussian_blur_sigmaX_line = 0  # 高斯模糊的标准差-直线
line_length = 100  # 显示拟合线段的长度
min_line_length = 60  # 霍夫直线变换的最小线段长度
max_line_gap = 20  # 霍夫直线变换的最大间隙
max_line_length = 120  # 检测线段的最大长度
rho = 1 # 表示霍夫变换中累加器的距离分辨率
voting_thresholds = 50 # 投票阈值

# 需要合并在一起的直线参数设置
angle_threshold = 5
distance_threshold = 10


def detect_largest_circle(image):
    """
    定义一个函数 detect_largest_circle，它接受一个参数 image，表示输入的图像。
    """
    # 将输入的彩色图像转换为灰度图像。cv2.cvtColor 是 OpenCV 库中的函数，用于颜色空间转换。
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # 对灰度图像应用高斯模糊。cv2.GaussianBlur 是 OpenCV 库中的函数，gaussian_blur_ksize 和 gaussian_blur_sigmaX 是高斯核的大小和标准差。
    blurred = cv2.GaussianBlur(gray, gaussian_blur_ksize, gaussian_blur_sigmaX)
    # Canny 边缘检测算法检测图像的边缘。canny_threshold1 和 canny_threshold2 是 Canny 算法的两个阈值。
    edges = cv2.Canny(blurred, canny_threshold1, canny_threshold2)
    # 使用霍夫变换检测图像中的圆形
    circles = cv2.HoughCircles(edges, cv2.HOUGH_GRADIENT, dp=hough_dp, minDist=hough_minDist,
                               param1=hough_param1, param2=hough_param2, minRadius=hough_minRadius, maxRadius=hough_maxRadius)
    # 检测是否为空
    if circles is not None:
        # 将检测到的圆形的坐标和半径四舍五入到整数，并转换为整数类型。
        circles = np.round(circles[0, :]).astype("int")
        # 找到半径最大的圆形。这里使用了 max 函数和 lambda 函数来比较每个圆的半径。
        largest_circle = max(circles, key=lambda c: c[2])
        return largest_circle # 返回最大的圆形的坐标和半径。
    else:
        return None

def detect_lines_in_circle(image, circle, max_line_length):
    """
    定义一个函数 detect_lines_in_circle，
    它接受三个参数：
    image（图像），
    circle（圆的坐标和半径），
    max_line_length（最大直线长度）。
    """
    mask = np.zeros_like(image)
    # 在遮罩图像上绘制一个圆，圆的中心是 circle[0], circle[1]，半径是 circle[2] * inner_circle_scale，颜色为白色，填充方式为填充。
    cv2.circle(mask, (circle[0], circle[1]), int(circle[2] * inner_circle_scale), (255, 255, 255), -1)
    # 将遮罩图像与原始图像进行位与操作，得到只包含圆内的像素的图像。
    masked_image = cv2.bitwise_and(image, mask)

    gray = cv2.cvtColor(masked_image, cv2.COLOR_BGR2GRAY)
    #对灰度图像应用高斯模糊。
    blurred = cv2.GaussianBlur(gray, gaussian_blur_ksize_line, gaussian_blur_sigmaX_line)
    edged = cv2.Canny(blurred, canny_threshold3, canny_threshold4)
    # 使用概率霍夫线变换检测图像中的直线
    lines = cv2.HoughLinesP(edged, rho, np.pi / 180, voting_thresholds, minLineLength=min_line_length, maxLineGap=max_line_gap)
    # 检测是否为空
    if lines is not None:
        # 过滤掉长度超过 max_line_length 的直线。
        filtered_lines = []
        for line in lines:
            x1, y1, x2, y2 = line[0]
            line_length = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
            if line_length <= max_line_length:
                filtered_lines.append(line)
        
        # 合并近似重合的直线
        merged_lines = merge_similar_lines(filtered_lines)
        return merged_lines
    return None

def merge_similar_lines(lines):
    """
    定义一个函数 merge_similar_lines，它接受一个参数 lines，表示检测到的直线列表。
    """
    merged_lines = []
    for line in lines:
        # 获取直线的起点和终点坐标，计算直线的斜率角度，并初始化一个标志变量 merged 为 False。
        x1, y1, x2, y2 = line[0]
        angle = calculate_slope_angle(x1, y1, x2, y2)
        merged = False
        # 对于每条已经合并的直线，计算其斜率角度，并与当前直线的斜率角度进行比较。
        # 如果角度差异小于 angle_threshold 并且起点或终点的距离小于 distance_threshold，则将两条直线合并。
        for merged_line in merged_lines:
            mx1, my1, mx2, my2 = merged_line[0]
            m_angle = calculate_slope_angle(mx1, my1, mx2, my2)
            if abs(angle - m_angle) < angle_threshold:
                if math.sqrt((mx1 - x1) ** 2 + (my1 - y1) ** 2) < distance_threshold or math.sqrt((mx2 - x2) ** 2 + (my2 - y2) ** 2) < distance_threshold:
                    merged_line[0] = [min(x1, mx1), min(y1, my1), max(x2, mx2), max(y2, my2)]
                    merged = True
                    break
        # 如果当前直线没有被合并，则将其添加到合并后的直线列表中。
        if not merged:
            merged_lines.append(line)
    return merged_lines


def calculate_slope_angle(x1, y1, x2, y2):
    """
    定义一个函数 calculate_slope_angle，它接受四个参数：直线的起点和终点坐标。
    """
    if x1 == x2:
        return 90
    # 计算直线的斜率
    slope = (y2 - y1) / (x2 - x1)
    # 将斜率转换为角度（度）
    angle = math.degrees(math.atan(slope))
    if angle < 0:
        angle += 180
    return angle


# 检测角度，计算温度
def calculate_temperature(avg_circle, x1, y1, x2, y2):
    """
    定义一个函数 calculate_temperature，它接受5个参数：圆的属性和直线的起点和终点坐标。
    """
    # 首先寻找一个直线的中心坐标，因为直线的起点或者终点都可能超过圆形的四个区域
    circle_center = [avg_circle[0], avg_circle[1]]  # 赋值圆心的坐标
    r = avg_circle[2]  # 赋值圆形的半径
    nx, my = (x1+x2)/2, (y1+y2)/2  # 计算直线的中点
    # 定义四个方位的划分界限坐标
    circle_left = [circle_center[0] - r, circle_center[1]]
    circle_on = [circle_center[0], circle_center[1] - r]
    circle_right = [circle_center[0] + r, circle_center[1]]
    circle_under = [circle_center[0], circle_center[1] + r]
    # 这个是指位于以圆形划分的四个区域的第一个区域（假设是第一象限，方便）

    if circle_left[0] <= nx <= circle_on[0] and circle_on[1] <= my <= circle_left[1]:
        # print("第一象限")
        if my == circle_center[1]:
            return -20
        elif nx == circle_center[0]:
            return 16
        else:
            # 计算角度
            theta = math.atan2(y2 - y1, x2 - x1)
            # 将角度从弧度转换为度(这里加上绝对值是因为区分了四个象限之后，对于角度正负不用理会)
            theta_degrees = abs(math.degrees(theta))
            # 第一象限的起步温度是-20度终点是16度， 0.39是70/180得到的每一个角度对应的温度值
            temperature = 0.39 * theta_degrees - 20
            return temperature

    # 第二象限
    elif circle_on[0] <= nx <= circle_right[0] and circle_on[1] <= my <= circle_right[1]:
        # print("第二象限")
        if my == circle_center[1]:
            return 50
        elif nx == circle_center[0]:
            return 16
        else:
            # 计算角度
            theta = math.atan2(y2 - y1, x2 - x1)
            # 将角度从弧度转换为度(这里加上绝对值是因为区分了四个象限之后，对于角度正负不用理会)
            theta_degrees = abs(math.degrees(theta))
            # 第二象限的起步温度是16度终点是50度， 0.39是70/180得到的每一个角度对应的温度值
            temperature = 50 - 0.39 * theta_degrees
            return temperature

    # # 第三象限
    elif circle_on[0] <= nx <= circle_right[0] and circle_left[1] <= my <= circle_under[1]:
        # print("第三象限")
        if my == circle_center[1]:
            return 50
        elif nx == circle_center[0]:
            return None
        else:
            # 计算角度
            theta = math.atan2(y2 - y1, x2 - x1)
            # 将角度从弧度转换为度(这里加上绝对值是因为区分了四个象限之后，对于角度正负不用理会)
            theta_degrees = abs(math.degrees(theta))
            # 第三象限的起步温度是50度终点是60度， 0.39是70/180得到的每一个角度对应的温度值
            temperature = 50 + 0.39 * theta_degrees
            return temperature

    # # 第四象限
    elif circle_left[0] <= nx <= circle_on[0] and circle_left[1] <= my <= circle_under[1]:
        # print("第四象限")
        if my == circle_center[1]:
            return -20
        elif nx == circle_center[0]:
            return None
        else:
            # 计算角度
            theta = math.atan2(y2 - y1, x2 - x1)
            # 将角度从弧度转换为度(这里加上绝对值是因为区分了四个象限之后，对于角度正负不用理会)
            theta_degrees = abs(math.degrees(theta))
            # 第四象限的起步温度是-20度终点是-30度， 0.39是70/180得到的每一个角度对应的温度值
            temperature = -20 - 0.39 * theta_degrees
            return temperature





