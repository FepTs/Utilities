"""
v1.1
用于重命名文件夹中的文件，支持指定后缀或重命名所有文件，
文件名格式化为五位数字，起始编号可自定义。
可以去除中文或混乱的文件名，统一格式。
bug已修复。
"""
import os

def rename_files(input_dir, ext_filter, start_number):
    # 检查输入文件夹是否存在
    if not os.path.isdir(input_dir):
        print(f"目录不存在: {input_dir}")
        return

    # 根据用户输入过滤文件
    if ext_filter.lower() not in ['', 'all']:
        # 用户输入后缀（例如jpg、png），不区分大小写
        ext_filter = ext_filter.lower()
        files = [f for f in os.listdir(input_dir) if f.lower().endswith('.' + ext_filter)]
    else:
        # 若不输入或输入'all'，则处理所有文件（只处理文件，不包含子目录）
        files = [f for f in os.listdir(input_dir) if os.path.isfile(os.path.join(input_dir, f))]

    if not files:
        print("未找到符合条件的文件。")
        return

    for idx, old_name in enumerate(files, start=start_number):
        # 格式化新文件名为五位数字字符串
        new_base = f"{idx:05d}"
        # 如果用户指定了后缀，则统一用该后缀，否则保持原始文件的后缀
        if ext_filter.lower() not in ['', 'all']:
            new_name = new_base + '.' + ext_filter
        else:
            # 提取旧文件的扩展名（包含点），若无扩展名则为空
            _, file_ext = os.path.splitext(old_name)
            new_name = new_base + file_ext

        old_path = os.path.join(input_dir, old_name)
        new_path = os.path.join(input_dir, new_name)

        try:
            os.rename(old_path, new_path)
            print(f"已重命名: {old_path} 为 {new_path}")
        except Exception as e:
            print(f"重命名 {old_path} 时出错: {e}")

def main(input_dir, ext_filter, start_number):
    rename_files(input_dir, ext_filter, start_number)

if __name__ == "__main__":
    # 在下面修改输入文件夹路径
    input_dir = r"C:/Users/Desktop/val/images"  # 输入文件夹路径
    # 输入需要处理的文件后缀（例如 jpg 或 png），若输入all则处理所有文件:
    ext_filter = "jpg"
    # 输入起始编号
    start_number = 1

    main(input_dir, ext_filter, start_number)
