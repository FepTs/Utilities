"""
v1.0
用于比较两个目录中文件名是否相同，可以用于检验标签文件或图像的丢失，支持一键删除多余文件
"""
import os


def get_file_names(folder_path):

    if not os.path.exists(folder_path) or not os.path.isdir(folder_path):
        print(f"错误: {folder_path} 不是有效的文件夹路径。")
        return set()

    return {os.path.splitext(file)[0] for file in os.listdir(folder_path) if
            os.path.isfile(os.path.join(folder_path, file))}


def confirm_and_delete(folder_path, extra_files):

    if not extra_files:
        return

    print(f"以下文件仅在 {folder_path} 中存在:")
    file_paths = []
    for file_name in extra_files:
        for f in os.listdir(folder_path):
            if os.path.splitext(f)[0] == file_name:
                file_paths.append(os.path.join(folder_path, f))
                break

    print("\n".join(file_paths))
    confirm = input("是否删除以上所有文件？(y/n): ")
    if confirm.lower() == 'y':
        for file_path in file_paths:
            os.remove(file_path)
        print("已删除所有多余文件")
    else:
        print("未删除任何文件。")


def compare_folders(folder1, folder2):
    """比较两个文件夹的文件名，并处理多余文件"""
    files1 = get_file_names(folder1)
    files2 = get_file_names(folder2)

    common_files = files1 & files2  # 交集，两个文件夹都存在的文件
    extra_in_folder1 = files1 - files2  # 仅在 folder1 中的文件
    extra_in_folder2 = files2 - files1  # 仅在 folder2 中的文件

    print(f"共有 {len(common_files)} 个文件在两个文件夹中都有。")
    print(f"{folder1} 中有 {len(extra_in_folder1)} 个额外文件。")
    print(f"{folder2} 中有 {len(extra_in_folder2)} 个额外文件。")

    # 处理额外文件
    if extra_in_folder1:
        confirm_and_delete(folder1, extra_in_folder1)

    if extra_in_folder2:
        confirm_and_delete(folder2, extra_in_folder2)


def main(folder1, folder2):
    compare_folders(folder1, folder2)


if __name__ == "__main__":
    # 需要修改的部分
    folder1 = r"C:\Users\val\images"  # 文件夹1路径
    folder2 = r"C:\Users\val\labels"  # 文件夹2路径
    main(folder1, folder2)
