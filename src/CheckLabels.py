"""
v1.2
用于清洗YOLO标注文件中的类别编号，并自动将保留的类别转换为连续的数字。
例如：只保留0、1、3类，原始标注中保留的0、1、3会映射为0、1、2，确保连续，避免训练时类别不连续的问题。
"""

import os


def clean_labels(folder_path, valid_classes):
    """
    遍历指定文件夹中的所有txt文件，逐行检查类标签：
    1. 只保留在 valid_classes 中的标注行；
    2. 自动将保留的原始类别映射为连续的类别编号。
    """
    if not os.path.exists(folder_path) or not os.path.isdir(folder_path):
        print(f"错误: {folder_path} 不是有效的文件夹路径。")
        return

    # 对有效类别进行排序，构建映射：原类别 -> 新连续类别（从0开始）
    sorted_classes = sorted(valid_classes)
    class_mapping = {orig: new for new, orig in enumerate(sorted_classes)}
    print("类别映射：", class_mapping)

    # 筛选文件夹中的txt文件
    file_list = [
        f for f in os.listdir(folder_path)
        if f.endswith('.txt') and os.path.isfile(os.path.join(folder_path, f))
    ]

    for file_name in file_list:
        file_path = os.path.join(folder_path, file_name)

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except Exception as e:
            print(f"无法读取文件 {file_name}，错误信息：{e}")
            continue

        modified = False
        valid_lines = []
        for line in lines:
            parts = line.strip().split()
            if not parts:
                continue
            try:
                orig_class = int(parts[0])
            except ValueError:
                # 类别标签不是整数则直接略过该行
                continue

            # 检查是否为保留类别
            if orig_class in class_mapping:
                # 替换首个元素为映射后的新类别编号，同时保留后面的信息
                new_class = class_mapping[orig_class]
                # 使用新的类别编号构造新行：注意其他部分保持不变
                new_line = ' '.join([str(new_class)] + parts[1:]) + '\n'
                valid_lines.append(new_line)
                # 判断是否有修改
                if new_class != orig_class:
                    modified = True
            else:
                # 标记删除行
                modified = True

        # 仅在标注行发生变动时更新文件内容
        if modified or len(valid_lines) != len(lines):
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.writelines(valid_lines)
                print(f"已清洗: {file_name}，保留 {len(valid_lines)} 行")
            except Exception as e:
                print(f"写入文件 {file_name} 时出错，错误信息：{e}")
        else:
            print(f"无变化: {file_name}")


def main(folder_path, valid_classes):
    clean_labels(folder_path, valid_classes)


if __name__ == "__main__":
    # 用户输入标注文件夹路径
    folder_path = input("请输入标注文件所在文件夹路径：").strip()
    # 用户输入需要保留的类别编号（以逗号分隔，例如：0,1,3）
    classes_str = input("请输入需要保留的类别编号（以逗号分隔，如 0,1,3）：").strip()
    try:
        valid_classes = [int(cls.strip()) for cls in classes_str.split(',') if cls.strip() != '']
    except ValueError:
        print("输入的类别编号格式不正确，请输入数字并以逗号分隔。")
        exit(1)

    main(folder_path, valid_classes)
