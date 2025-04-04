"""
v1.0
用于清洗YOLO标注文件中的类别编号
例如：仅需要0、1类，某个标注文件中包含类别2、4、5的行，将被清除，仅保留合法的0或1类数据。
"""
import os


def clean_labels(folder_path):
    """
    遍历指定文件夹中的所有txt文件，逐行检查类标签，
    只保留对应类标签的标注行，其它行将被删除。
    """
    if not os.path.exists(folder_path) or not os.path.isdir(folder_path):
        print(f"错误: {folder_path} 不是有效的文件夹路径。")
        return

    file_list = [f for f in os.listdir(folder_path) if f.endswith('.txt') and os.path.isfile(os.path.join(folder_path, f))]

    for file_name in file_list:
        file_path = os.path.join(folder_path, file_name)

        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        valid_lines = []
        for line in lines:
            parts = line.strip().split()
            if not parts:
                continue
            try:
                class_id = int(parts[0])
                # 在这里修改需要的类别编号
                if class_id in [0, 1]:
                    valid_lines.append(line)
            except ValueError:
                # 类别标签不是整数的行自动忽略
                continue

        # 仅在有修改时才重写文件
        if len(valid_lines) != len(lines):
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(valid_lines)
            print(f"已清洗: {file_name}，保留 {len(valid_lines)} 行")
        else:
            print(f"无变化: {file_name}")


def main(folder_path):
    clean_labels(folder_path)


if __name__ == "__main__":
    # 需要修改的部分：修改为你的标注文件所在文件夹路径
    folder_path = r"E:\Project\yolo\dataset\ParkingViolations_4output_perfect\ParkingViolations_4output_perfect\ParkingViolations_4output_perfect\train\labels"  # 标注文件夹路径
    main(folder_path)
