"""
v1.0
用于比较两个目录中文件名是否存在对应的标注文件，
如果第二个目录不包含与第一个目录中同名（不包括后缀）的标注文件，则在第二个目录生成一个空白txt文件。
例如：文件夹一中包含 001.jpg、002.jpg，文件夹二中包含 001.txt、classes.txt，
则会在文件夹二中生成一个空白的 002.txt 文件。
"""
import os


def create_blank_annotation_files(folder1, folder2):
    """
    遍历 folder1 中的文件，对于每个文件，检查 folder2 中是否存在与之同名（不含后缀）的txt文件，
    如果不存在，则在 folder2 中生成一个空白的txt文件。
    """
    if not os.path.exists(folder1) or not os.path.isdir(folder1):
        print(f"错误: {folder1} 不是有效的文件夹路径。")
        return

    if not os.path.exists(folder2) or not os.path.isdir(folder2):
        print(f"错误: {folder2} 不是有效的文件夹路径。")
        return

    for file in os.listdir(folder1):
        file_path = os.path.join(folder1, file)
        if os.path.isfile(file_path):
            basename, _ = os.path.splitext(file)
            annotation_path = os.path.join(folder2, basename + ".txt")
            if os.path.exists(annotation_path):
                # 如果 folder2 中已存在对应的标注文件则跳过
                continue
            else:
                # 在 folder2 中生成空白的txt文件
                with open(annotation_path, 'w', encoding='utf-8') as f:
                    pass
                print(f"已创建: {annotation_path}")


def main(folder1, folder2):
    create_blank_annotation_files(folder1, folder2)


if __name__ == "__main__":
    # 需要修改的部分：修改为你的实际文件夹路径
    folder1 = r"E:\Project\yolo\dataset\ParkingViolations_4output_perfect\ParkingViolations_4output_perfect\ParkingViolations_4output_latest\val\images"  # 文件夹1路径（包含图片等文件）
    folder2 = r"E:\Project\yolo\dataset\ParkingViolations_4output_perfect\ParkingViolations_4output_perfect\ParkingViolations_4output_latest\val\labels"  # 文件夹2路径（包含标注txt文件）
    main(folder1, folder2)
