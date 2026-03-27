
import numpy as np
import json
import math

def predict_distance(x1, x2, x3, x4, y1, y2, y3, y4) -> float:
    # with open('ridge_regression_model.json', 'r') as file:
    #     model_data = json.load(file)

    model_data = {
    "equation": "y = e^( - 0.004*x1 - 0.007*x2 - 0.000*x1^2 + 0.000*x1 x2 - 0.000*x2^2 + 5.514)",
    "description": "\u8fd9\u662f\u4f7f\u7528\u5177\u6709\u591a\u9879\u5f0f\u7279\u5f81\u7684\u5cad\u56de\u5f52\u9884\u6d4b\u57fa\u4e8e x1 \u548c x2 \u7684\u5b9e\u9645\u8ddd\u79bb\u7684\u6a21\u578b\u65b9\u7a0b\u3002",
    "r_square_log": 0.994877034295452,
    "model_parameters": {
        "coefficients": [
            -0.004067305655731796,
            -0.006693224559602325,
            -0.00012876435160600512,
            9.590659661135591e-05,
            -1.1131910088514775e-05
        ],
        "intercept": 5.5139729579962085
    },
    "features": [
        "x1",
        "x2",
        "x1^2",
        "x1 x2",
        "x2^2"
    ]
}


    coefficients = np.array(model_data['model_parameters']['coefficients'])
    intercept = model_data['model_parameters']['intercept']
    # print(coefficients, intercept)
    """根据多项式特征计算预测距离"""
    distance1 = int(math.sqrt((y2 - y1) ** 2 + (x2 - x1) ** 2))
    distance2 = int(math.sqrt((y4 - y3) ** 2 + (x4 - x3) ** 2))

    features = [distance1, distance2, distance1**2, distance1*distance2, distance2**2]
    features = np.array(features)  # 确保特征是numpy数组
    y_log_predicted = np.dot(features, coefficients) + intercept
    distance_predicted = np.exp(y_log_predicted)  # 取指数获得原始距离
    return distance_predicted


def predict_angle(x_val, y_val):
    # 广角摄像头一半的的角度
    camera_anlge = 60 / 2
    # 图像中心的坐标
    center = [320, 240]
    # 手部矩形框与中心点的坐标差值，（△x，△y）
    center_df = [center[0]-x_val, center[1]-y_val]
    # print(center_df)
    # 矩形框中心点坐标差△x乘以每一个像素对应的广角摄像头的角度值
    angle_x = -center_df[0] * (camera_anlge / center[0])
    # angle_x = center_df[0] * (camera_anlge / center[0])
    # 同理可得垂直方向的
    angle_y = center_df[1] * (camera_anlge / center[1])

    return [angle_x, angle_y]
