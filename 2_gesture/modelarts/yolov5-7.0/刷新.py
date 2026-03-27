import os
import shutil
import random

# 从机械狗收集到的源文件夹的基础路径
base_source_path = r"D:\YSW\人工智能-机械狗\手势识别场景\yolov5-7.0\dataset\train_images"

# 目标文件夹路径
train_destination_path = r"D:\YSW\人工智能-机械狗\手势识别场景\yolov5-7.0\dataset\images\train"
val_destination_path = r"D:\YSW\人工智能-机械狗\手势识别场景\yolov5-7.0\dataset\images\val"

# 确保目标文件夹存在
os.makedirs(train_destination_path, exist_ok=True)
os.makedirs(val_destination_path, exist_ok=True)

# 遍历每个数字命名的文件夹（例如，1, 2, 3, 4, 5）
for folder_name in range(1, 6):
    current_folder = os.path.join(base_source_path, str(folder_name))
    all_files = os.listdir(current_folder)

    # 重命名并移动文件到训练集目标目录
    for file_count, filename in enumerate(all_files, 1):
        file_path = os.path.join(current_folder, filename)
        new_filename = f"{folder_name}({file_count}).jpg"
        destination_file_path = os.path.join(train_destination_path, new_filename)
        shutil.copy(file_path, destination_file_path)  # 首先复制到目标目录
        print(f"Copied: {file_path} to {destination_file_path}")

# 接下来，从train_destination_path移动部分图片到val_destination_path
all_train_files = os.listdir(train_destination_path)
random.shuffle(all_train_files)
num_val_files = int(0.2 * len(all_train_files))  # 假设20%的文件应该是验证集
val_files = all_train_files[:num_val_files]

for filename in val_files:
    source_file_path = os.path.join(train_destination_path, filename)
    destination_file_path = os.path.join(val_destination_path, filename)
    shutil.move(source_file_path, destination_file_path)  # 然后移动到验证集目录
    print(f"Moved to val: {source_file_path} to {destination_file_path}")