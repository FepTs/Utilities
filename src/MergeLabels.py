"""
v1.0
用于合并两个目录下同名标注文件的内容。
遍历文件夹1和文件夹2中所有txt文件，
对于在两个文件夹中同名的txt文件，将文件夹2中的内容合并追加到文件夹1对应的文件中。
"""
import os


def merge_annotation_files(folder1, folder2):
    """
    遍历两个文件夹中的所有txt文件，查找同名文件，
    并将文件夹2中的内容合并到文件夹1中的对应文件后面。
    """
    if not os.path.exists(folder1) or not os.path.isdir(folder1):
        print(f"错误: {folder1} 不是有效的文件夹路径。")
        return

    if not os.path.exists(folder2) or not os.path.isdir(folder2):
        print(f"错误: {folder2} 不是有效的文件夹路径。")
        return

    # 获取两个文件夹中所有的txt文件，key为文件名（不含扩展名），value为完整文件名
    files1 = {os.path.splitext(f)[0]: f for f in os.listdir(folder1)
              if f.endswith('.txt') and os.path.isfile(os.path.join(folder1, f))}
    files2 = {os.path.splitext(f)[0]: f for f in os.listdir(folder2)
              if f.endswith('.txt') and os.path.isfile(os.path.join(folder2, f))}

    # 找出两个文件夹中同名的txt文件
    common_files = set(files1.keys()) & set(files2.keys())
    if not common_files:
        print("没有找到同名的标注文件，无需合并。")
        return

    for basename in common_files:
        file1_path = os.path.join(folder1, files1[basename])
        file2_path = os.path.join(folder2, files2[basename])

        # 读取文件夹2中的内容
        with open(file2_path, 'r', encoding='utf-8') as f2:
            content2 = f2.read()

        # 如果文件夹2中的内容非空，则合并到文件夹1中
        if content2.strip():
            with open(file1_path, 'a', encoding='utf-8') as f1:
                # 检查文件夹1中的文件是否以换行结束，如果没有，则添加一个换行
                f1.seek(0, os.SEEK_END)
                if f1.tell() > 0:
                    f1.seek(f1.tell() - 1)
                    if f1.read(1) != "\n":
                        f1.write("\n")
                f1.write(content2)
            print(f"合并文件: {files1[basename]}")
        else:
            print(f"文件 {files2[basename]} 内容为空，跳过合并。")


def main(folder1, folder2):
    merge_annotation_files(folder1, folder2)


if __name__ == "__main__":
    # 需要修改的部分：修改为你的实际文件夹路径
    folder1 = r"C:\Users\labels01"  # 文件夹1路径（目标标注文件目录）
    folder2 = r"C:\Users\labels2345"  # 文件夹2路径（待合并的标注文件目录）
    main(folder1, folder2)
