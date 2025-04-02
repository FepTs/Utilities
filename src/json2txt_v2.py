"""
v1.0
转换为 YOLO 适用的 txt 格式
"""
import os
import json
import glob


def convert_json_to_yolo(json_path, output_path, label_mapping):

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 获取图像的宽度和高度
    image_width = data.get("imageWidth")
    image_height = data.get("imageHeight")
    if image_width is None or image_height is None:
        print(f"Warning: 文件 {json_path} 中缺少 imageWidth/imageHeight 信息，跳过该文件。")
        return

    lines = []
    for shape in data.get("shapes", []):
        # 仅处理矩形标注，若有需要，可添加其他形状的处理
        if shape.get("shape_type") != "rectangle":
            continue

        label = shape.get("label")
        if label not in label_mapping:
            print(f"Warning: 在文件 {json_path} 中，未在类别映射中找到标签 {label}，跳过该标注。")
            continue

        # 计算最小和最大的坐标值
        points = shape.get("points", [])
        if len(points) < 2:
            print(f"Warning: 文件 {json_path} 中的标注 {shape} 点数不足，跳过。")
            continue

        x_coords = [p[0] for p in points]
        y_coords = [p[1] for p in points]
        x_min, x_max = min(x_coords), max(x_coords)
        y_min, y_max = min(y_coords), max(y_coords)

        # 计算中心点和宽高
        center_x = (x_min + x_max) / 2.0
        center_y = (y_min + y_max) / 2.0
        bbox_width = x_max - x_min
        bbox_height = y_max - y_min

        # 归一化
        center_x_norm = center_x / image_width
        center_y_norm = center_y / image_height
        width_norm = bbox_width / image_width
        height_norm = bbox_height / image_height

        # YOLO 格式：class_id center_x center_y width height（归一化坐标）
        class_id = label_mapping[label]
        line = f"{class_id} {center_x_norm:.6f} {center_y_norm:.6f} {width_norm:.6f} {height_norm:.6f}"
        lines.append(line)

    # 写入输出文件
    with open(output_path, 'w', encoding='utf-8') as f_out:
        for line in lines:
            f_out.write(line + "\n")
    print(f"转换完成：{json_path} -> {output_path}")


def main(input, output, map):
    # 如果输出文件夹不存在，则创建
    if not os.path.exists(output):
        os.makedirs(output)

    # 获取文件夹中所有 .json 文件
    json_files = glob.glob(os.path.join(input, "*.json"))
    if not json_files:
        print("没有找到 JSON 文件，请检查文件夹路径。")
        return

    # 对每个 JSON 文件进行转换
    for json_file in json_files:
        base_name = os.path.splitext(os.path.basename(json_file))[0]
        txt_file = os.path.join(output, base_name + ".txt")
        convert_json_to_yolo(json_file, txt_file, map)


if __name__ == "__main__":
    # JSON 标注文件所在的文件夹路径
    json_folder = "C:/Users/Desktop/labels"
    # 保存转换后 TXT 文件的文件夹路径
    txt_folder = "C:/Users/Desktop/newlabels"
    # 类别映射
    label_mapping = {
        "line": 0,
        "car": 1
    }
    main(json_folder, txt_folder, label_mapping)
