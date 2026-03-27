#
# import logging
#
# logging.basicConfig(level=logging.DEBUG)
#
# actions_name = {
#     1: '直走（0.3表示前进0.3米，-0.3表示后退0.3米）',
#     2: '平移（0.3表示右平移0.3米，-0.3表示左平移0.3米）',
#     3: '旋转（45表示向右旋转45度，-45表示向做旋转45度）'
# }
#
# actions_params = {}
# actions_sequence = []
# val1, val2, val3 = [], [], []
#
# print("下面即将进入到输入环节，根据你输入的数字和参数索引，机械狗将会做出相应运动")
# print("输入格式：动作ID,参数索引，例如：3,2,1,2,3,1（依次用英文逗号分隔开）")
#
# x = input("请输入动作ID(回车结束)：")
# x = x.split(',')
# x = [i for i in x if i != '']
# for action_id in x:
#
#     actions_sequence.append((int(action_id), 0))  # 假设总是使用参数列表中的第一个参数
# def update_actions_sequence(actions_sequence):
#     # 初始化计数器
#     count_1 = 0
#     count_2 = 0
#     count_3 = 0
#
#     # 结果列表
#     updated_sequence = []
#
#     # 遍历原始序列
#     for action in actions_sequence:
#         if action[0] == 3:
#             # 如果是3，更新3的计数器
#             updated_sequence.append((3, count_3))
#             count_3 += 1
#         elif action[0] == 1:
#             # 如果是1，更新1的计数器
#             updated_sequence.append((1, count_1))
#             count_1 += 1
#         elif action[0] == 2:
#             # 如果是2，更新2的计数器
#             updated_sequence.append((2, count_2))
#             count_2 += 1
#     return updated_sequence
#
# actions_sequence = update_actions_sequence(actions_sequence)
#
# logging.info('这里可以设置速度挡位，比如在显示前进的时候可以出入  0.3,6   意思是以6档的速度前进0.3米')
#
# for index, action in enumerate(actions_sequence):
#     action_name = actions_name.get(action[0], "未知动作")
#     print(f'第{index+1}个动作是：{action_name}')
#     vals = input('你想要做的操作是：')
#
#     # 检查是否包含逗号
#     if ',' in vals:
#         # 如果包含逗号，则将输入按逗号分割
#         vals = vals.split(',')
#         # 转换每个分割项为浮点数
#         vals = tuple(float(val.strip()) for val in vals)
#     else:
#         # 如果没有逗号，则直接转换为浮点数
#         vals = (float(vals),)
#
#     print(vals)
#
#     if action[0] == 1:
#         val1.append(vals,)
#     elif action[0] == 2:
#         val2.append(vals,)
#     elif action[0] == 3:
#         val3.append(vals,)
#
# actions_params = {
#     1: val1,
#     2: val2,
#     3: val3,
# }
#
# print(actions_params)

x = 361

def angle_remainder(x):
    if x > 360:
        x = x / (x % 360)
        return x
    else:
        return x


print(angle_remainder(x))
