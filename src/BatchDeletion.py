"""
v1.0
用于批量删除指定文件夹中包含特定字符特征的文件，
例如文件名包含 '*'、'()' 或 'train' 等字符。
"""
import os


def delete_files(input_folder, feature, extension):

    # 获取文件夹中所有符合条件的文件
    files = [f for f in os.listdir(input_folder) if feature in f and f.endswith(extension)]

    if not files:
        print("没有找到符合条件的文件。")
        return

    # 批量删除文件
    for file in files:
        file_path = os.path.join(input_folder, file)
        try:
            os.remove(file_path)
            print(f"已删除: {file_path}")
        except Exception as e:
            print(f"删除 {file_path} 失败: {e}")


def main(input_folder, feature, extension):
    delete_files(input_folder, feature, extension)


if __name__ == "__main__":

    folder = input("请输入文件夹路径: ").strip()
    feature = input("请输入文件名中包含的特征字符: ").strip()
    extension = input("请输入文件后缀名（例如 '.txt', '.jpg' 等）: ").strip()

    main(folder, feature, extension)
