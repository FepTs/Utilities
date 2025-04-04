"""
v1.1
用于清洗YOLO标注文件中的类别编号
例如：仅需要0、1类，某个标注文件中包含类别2、4、5的行将被清除，仅保留合法的标注数据。
"""
import os


def clean_labels(folder_path, valid_classes):
    """
    遍历指定文件夹中的所有txt文件，逐行检查类标签，
    只保留在 valid_classes 列表中的标注行，其它行将被删除。
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
                if class_id in valid_classes:
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


def main(folder_path, valid_classes):
    clean_labels(folder_path, valid_classes)


if __name__ == "__main__":
    # 用户输入标注文件夹路径
    folder_path = input("请输入标注文件所在文件夹路径：").strip()
    # 用户输入需要保留的类别编号（以逗号分隔，例如：0,1）
    classes_str = input("请输入需要保留的类别编号（以逗号分隔，如 0,1）：").strip()
    try:
        valid_classes = [int(cls.strip()) for cls in classes_str.split(',') if cls.strip() != '']
    except ValueError:
        print("输入的类别编号格式不正确，请输入数字并以逗号分隔。")
        exit(1)

    main(folder_path, valid_classes)
