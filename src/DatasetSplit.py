"""
v0.1
用于图像分割数据集的制作
"""
import os
import shutil
import random

def create_dir_structure(output_path, class_names):
    """创建训练和验证的目录结构"""
    for subset in ['train', 'val']:
        for class_name in class_names:
            os.makedirs(os.path.join(output_path, subset, class_name), exist_ok=True)


def split_dataset(original_path, output_path, train_ratio):
    """划分数据集并组织成训练和验证集"""
    class_names = os.listdir(original_path)
    create_dir_structure(output_path, class_names)

    for class_name in class_names:
        class_path = os.path.join(original_path, class_name)
        if not os.path.isdir(class_path):
            continue  # 跳过非目录文件

        images = os.listdir(class_path)
        random.shuffle(images)  # 随机打乱图片顺序

        # 划分训练集和验证集
        split_idx = int(len(images) * train_ratio)
        train_images = images[:split_idx]
        val_images = images[split_idx:]

        # 复制到目标文件夹
        for img in train_images:
            shutil.copy(os.path.join(class_path, img),
                        os.path.join(output_path, 'train', class_name, img))
        for img in val_images:
            shutil.copy(os.path.join(class_path, img),
                        os.path.join(output_path, 'val', class_name, img))


def main(original_dataset_path, output_dataset_path, train_ratio):
    # 检查原始数据集路径是否存在
    if not os.path.exists(original_dataset_path):
        print(f"原始数据集路径 {original_dataset_path} 不存在！")
    else:
        # 删除已有的输出目录，避免干扰
        if os.path.exists(output_dataset_path):
            shutil.rmtree(output_dataset_path)

        # 划分数据集
        split_dataset(original_dataset_path, output_dataset_path, train_ratio)
        print(f"数据集已划分完成，结果保存在 {output_dataset_path}")


if __name__ == "__main__":
    # 数据集路径
    input = r"C:/Users/Desktop/dataset/"  # 原始数据集目录
    output = r"./output"  # 输出数据集目录
    # 设置划分比例
    ratio = 0.8

    main(input, output, ratio)

