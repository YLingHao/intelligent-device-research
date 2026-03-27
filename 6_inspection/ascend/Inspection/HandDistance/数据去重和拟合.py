# import pandas as pd
#
# # 定义数据
# data = pd.read_csv('test - 副本.csv')
#
# # 创建DataFrame
# df = pd.DataFrame(data)
#
# # 去重
# unique_df = df.drop_duplicates(subset=['5_17', '0_12'])
#
# # 根据所有列去除重复行
# unique_df_all = df.drop_duplicates()
#
# # 导出数据到CSV
# unique_df.to_csv('unique_data.csv', index=False)



import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.preprocessing import PolynomialFeatures
import matplotlib.pyplot as plt
from sklearn.pipeline import make_pipeline

plt.rcParams['font.sans-serif'] = ['SimHei']    # 用来正常显示中文标签
plt.rcParams['axes.unicode_minus'] = False      # 用来正常显示负号

data = pd.read_csv('unique_data.csv')
x1, x2 = data['5_17'], data['0_12']
y = data['real_distance']
X = np.column_stack((x1, x2))

# 对 y 进行自然对数变换
y_log = np.log(y)

# 创建多项式特征
poly = PolynomialFeatures(degree=2, include_bias=False)
X_poly = poly.fit_transform(X)

# 分割数据
X_train, X_test, y_train_log, y_test_log = train_test_split(X_poly, y_log, test_size=0.2, random_state=42)

# 使用Ridge回归模型
model = Ridge(alpha=1.0)
model.fit(X_train, y_train_log)

# 预测
y_log_pred = model.predict(X_test)
y_pred = np.exp(y_log_pred)
r_square_log = model.score(X_test, y_test_log)
print("对数转换和多项式特征后的Ridge模型的 R^2 Score:", r_square_log)

# 输出模型的参数
coef = model.coef_
intercept = model.intercept_
print("模型的系数为:", coef)
print("模型的截距为:", intercept)

# 创建一个管道，包含多项式特征和Ridge回归模型  L2正则
pipeline = make_pipeline(PolynomialFeatures(degree=2, include_bias=False), Ridge(alpha=1.0))
pipeline.fit(X_train, y_train_log)


# 获取多项式特征的名称

features = poly.get_feature_names_out(['x1', 'x2'])

# 开始构建方程式
equation = "y = e^("
for i, feature in enumerate(features):
    if coef[i] > 0 and i > 0:  # 处理正系数
        equation += " + "
    elif coef[i] < 0:  # 处理负系数
        equation += " - "
    equation += f"{abs(coef[i]):.3f}*{feature}"
equation += f" + {intercept:.3f})"

# 打印方程式
print(equation)

# 绘图
plt.scatter(X_test[:, 0], np.exp(y_test_log), color='blue', label='实际值')
plt.scatter(X_test[:, 0], y_pred, color='red', alpha=0.5, label='预测值')
plt.title('Ridge回归的实际值与预测值\n' + equation)
plt.xlabel('X1 (特征值)')
plt.ylabel('Y (目标值)')
plt.legend()
plt.show()


import json

# 构建模型数据和方程式的字典
model_data = {
    "equation": equation,
    "description": "这是使用具有多项式特征的岭回归预测基于 x1 和 x2 的实际距离的模型方程。",
    "r_square_log": r_square_log,  # 存储R^2分数
    "model_parameters": {
        "coefficients": coef.tolist(),  # 将Numpy数组转换为列表
        "intercept": intercept
    },
    "features": features.tolist()  # 确保特征名称以适当的格式存储
}

# 写入模型数据到JSON文件
with open('ridge_regression_model.json', 'w') as file:
    json.dump(model_data, file, indent=4)

print("模型方程式和参数已成功保存到JSON文件。")