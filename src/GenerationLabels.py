"""
v0.1
用于给所有图片生成相同测试标签
"""
import os

# 输入文件夹路径和输出文件夹路径
input_folder = "C:/Users/Desktop/temp/train/images"
output_folder = "C:/Users/Desktop/temp/train/labels"

# 确保输出文件夹存在
os.makedirs(output_folder, exist_ok=True)

# 定义标签内容
label_content = '0 0.503846 0.515625 0.992308 0.968750'

# 遍历输入文件夹中的所有文件
for filename in os.listdir(input_folder):
    # 获取文件名（不含后缀）
    file_name_without_ext = os.path.splitext(filename)[0]
    # 创建对应的.txt文件路径
    label_file_path = os.path.join(output_folder, f'{file_name_without_ext}.txt')
    # 写入标签内容
    with open(label_file_path, 'w') as label_file:
        label_file.write(label_content)

print(f'标记文件已成功生成，共生成 {len(os.listdir(input_folder))} 个标记文件。')