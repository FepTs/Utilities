"""
v1.0
转换为 YOLO 适用的 txt 格式
不再维护
"""
import json
import os


def convert(img_size, box):
    dw = 1. / (img_size[0])
    dh = 1. / (img_size[1])
    x = (box[0] + box[2]) / 2.0 - 1
    y = (box[1] + box[3]) / 2.0 - 1
    w = box[2] - box[0]
    h = box[3] - box[1]
    x = x * dw
    w = w * dw
    y = y * dh
    h = h * dh
    return (x, y, w, h)


def decode_json(input, output, json_name, name2id):
    # 确保 output 目录存在
    if not os.path.exists(output):
        os.makedirs(output)

    txt_name = os.path.join(output, json_name[:-5] + '.txt')
    txt_file = open(txt_name, 'w', encoding='utf-8')

    json_path = os.path.join(input, json_name)
    data = json.load(open(json_path, 'r', encoding='gb2312'))

    img_w = data['imageWidth']
    img_h = data['imageHeight']

    for i in data['shapes']:
        label_name = i['label']
        if i['shape_type'] == 'rectangle':
            x1 = int(i['points'][0][0])
            y1 = int(i['points'][0][1])
            x2 = int(i['points'][1][0])
            y2 = int(i['points'][1][1])

            bb = (x1, y1, x2, y2)
            bbox = convert((img_w, img_h), bb)
            txt_file.write(str(name2id[label_name]) + " " + " ".join([str(a) for a in bbox]) + '\n')

    txt_file.close()


def main(input, output, map):
    json_names = os.listdir(input)
    for json_name in json_names:
        decode_json(input, output, json_name, map)


if __name__ == "__main__":

    input = 'C:/Users/Desktop/dataset/labels'
    output = 'C:/Users/Desktop/dataset/labelsnew'
    map = {'line': 0, 'car': 1}
    main(input, output, map)
