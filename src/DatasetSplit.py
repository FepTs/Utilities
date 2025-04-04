"""
v1.1
用于数据集制作，支持目标检测和目标分类任务。

目标检测任务：
输入路径下需包含 images/ 和 labels/ 两个文件夹，图像文件与标注文件一一对应，
按照用户设定的比例划分为 train/ 和 val/ 两个子集，每个子集中包含 images/ 和 labels/ 文件夹。
划分后输出目录结构如下：
output/
├── train/
│   ├── images/
│   │   ├── img1.jpg
│   │   └── ...
│   └── labels/
│       ├── img1.txt
│       └── ...
└── val/
    ├── images/
    │   └── ...
    └── labels/
        └── ...

目标分类任务：
输入路径下每个子文件夹代表一个类别，
划分后输出目录结构如下：
output/
├── train/
│   ├── class1/
│   │   ├── img1.jpg
│   │   └── ...
│   └── class2/
│       └── ...
└── val/
    ├── class1/
    │   └── ...
    └── class2/
        └── ...
"""
import os
import shutil
import random

# ------------------ 目标检测任务相关函数 ------------------
def create_detection_dir_structure(output_path):
    """创建目标检测数据集的目录结构：train/ 和 val/，每个目录下均包含 images/ 和 labels/"""
    for subset in ['train', 'val']:
        for subfolder in ['images', 'labels']:
            os.makedirs(os.path.join(output_path, subset, subfolder), exist_ok=True)


def split_detection_dataset(input_path, output_path, train_ratio):
    """
    划分目标检测数据集。
    输入路径下需包含 images/ 和 labels/ 两个文件夹，且文件一一对应。
    根据 train_ratio 划分训练集与验证集，并复制对应文件到输出目录中。
    """
    images_dir = os.path.join(input_path, 'images')
    labels_dir = os.path.join(input_path, 'labels')

    if not os.path.exists(images_dir) or not os.path.isdir(images_dir):
        print(f"错误: {images_dir} 不是有效的文件夹路径。")
        return

    if not os.path.exists(labels_dir) or not os.path.isdir(labels_dir):
        print(f"错误: {labels_dir} 不是有效的文件夹路径。")
        return

    # 获取所有图像文件，确保对应的标注文件存在
    image_files = []
    for file in os.listdir(images_dir):
        image_path = os.path.join(images_dir, file)
        if os.path.isfile(image_path):
            basename, _ = os.path.splitext(file)
            label_file = basename + ".txt"
            label_path = os.path.join(labels_dir, label_file)
            if os.path.exists(label_path):
                image_files.append(file)
            else:
                print(f"警告: {file} 找不到对应的标注文件，已跳过。")

    if not image_files:
        print("没有找到符合条件的图像和标注文件。")
        return

    # 随机打乱文件顺序
    random.shuffle(image_files)

    # 划分训练集和验证集
    split_idx = int(len(image_files) * train_ratio)
    train_files = image_files[:split_idx]
    val_files = image_files[split_idx:]

    # 复制文件到目标目录
    for file in train_files:
        basename, _ = os.path.splitext(file)
        src_img = os.path.join(images_dir, file)
        src_label = os.path.join(labels_dir, basename + ".txt")
        dst_img = os.path.join(output_path, 'train', 'images', file)
        dst_label = os.path.join(output_path, 'train', 'labels', basename + ".txt")
        shutil.copy(src_img, dst_img)
        shutil.copy(src_label, dst_label)

    for file in val_files:
        basename, _ = os.path.splitext(file)
        src_img = os.path.join(images_dir, file)
        src_label = os.path.join(labels_dir, basename + ".txt")
        dst_img = os.path.join(output_path, 'val', 'images', file)
        dst_label = os.path.join(output_path, 'val', 'labels', basename + ".txt")
        shutil.copy(src_img, dst_img)
        shutil.copy(src_label, dst_label)

    print(f"目标检测数据集划分完成：训练集 {len(train_files)} 个样本，验证集 {len(val_files)} 个样本。")

# ------------------ 目标分类任务相关函数 ------------------
def create_classification_dir_structure(output_path, class_names):
    """创建训练和验证的目录结构，每个类别一个子文件夹"""
    for subset in ['train', 'val']:
        for class_name in class_names:
            os.makedirs(os.path.join(output_path, subset, class_name), exist_ok=True)


def split_classification_dataset(original_path, output_path, train_ratio):
    """
    划分目标分类数据集。
    原始数据集目录下每个子文件夹代表一个类别，
    按照 train_ratio 划分为训练集和验证集，并复制文件到目标目录中。
    """
    class_names = os.listdir(original_path)
    create_classification_dir_structure(output_path, class_names)

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
    print("目标分类数据集划分完成。")

# ------------------ 主函数 ------------------
def main(input_path, output_path, train_ratio, task):
    """
    根据任务模式调用相应的数据集划分函数
    '0'代表目标检测，'1'代表目标分类
    """
    # 删除已有的输出目录，避免干扰
    if os.path.exists(output_path):
        shutil.rmtree(output_path)

    if task == '0':
        # 目标检测任务：输入目录需包含 images/ 和 labels/ 文件夹
        create_detection_dir_structure(output_path)
        split_detection_dataset(input_path, output_path, train_ratio)
        print(f"目标检测数据集已生成，结果保存在 {output_path}")
    elif task == '1':
        # 目标分类任务：输入目录下每个子文件夹代表一个类别
        split_classification_dataset(input_path, output_path, train_ratio)
        print(f"目标分类数据集已生成，结果保存在 {output_path}")
    else:
        print("无效的任务选择，请输入 0 或 1。")

# ------------------ 程序入口 ------------------
if __name__ == "__main__":
    print("请输入所有参数：")
    input_path = input("原始数据集路径：").strip()
    output_path = input("输出数据集路径：").strip()
    try:
        ratio = float(input("训练集占比（例如0.8代表80%的样本作为训练集）：").strip())
    except ValueError:
        print("训练集占比输入无效，请输入数字。")
        exit(1)
    print("任务类型：输入 0 代表目标检测任务，输入 1 代表目标分类任务")
    task = input("请输入任务类型 (0/1)：").strip()

    main(input_path, output_path, ratio, task)
