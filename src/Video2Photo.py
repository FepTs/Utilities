"""
v1.1
用于视频转图片,opencv速度稍快于iio,若您不愿使用opencv,请使用52行后的v1.1x版本
更新文件名为五位数，修复中文路径无法正确保存的bug
"""
import os
import cv2

def save_image(image, folder, num):
    # 拼接图片完整路径，文件名为“00001.jpg”格式（五位数字）
    filename = str(num).zfill(5) + '.jpg'
    address = os.path.join(folder, filename)
    # 通过 imencode 编码图片，再用二进制写入文件，解决中文路径问题
    result, encoded_img = cv2.imencode('.jpg', image)
    if result:
        with open(address, mode='wb') as f:
            f.write(encoded_img.tobytes())
    else:
        print(f"编码图片失败：{address}")

def main(input_video, start, timeF):
    # 读取视频文件
    videoCapture = cv2.VideoCapture(input_video)
    # 获取视频所在的目录
    video_dir = os.path.dirname(input_video)
    # 定义保存图片的目录为视频所在目录下的 images 文件夹
    images_dir = os.path.join(video_dir, "images")
    # 如果 images 目录不存在，则创建
    if not os.path.exists(images_dir):
        os.makedirs(images_dir)

    # 读取第一帧
    success, frame = videoCapture.read()
    cnt = 0  # 计数器

    while success:
        cnt += 1
        if cnt % timeF == 0:
            start += 1
            save_image(frame, images_dir, start)  # 保存至 images 文件夹
            print('save image:', cnt, 'Picture name:', str(start).zfill(5))
        success, frame = videoCapture.read()

if __name__ == '__main__':
    # 在下面修改输入视频路径、起始数字和每隔多少帧保存一张图片
    input_video = r"C:/Users/test.mp4"
    start = 0  # 文件名起始数字，不包括该数
    timeF = 10     # 每隔 timeF 帧保存一张图片
    main(input_video, start, timeF)


"""
v1.1x
使用体量更小的库的版本，若您不愿安装opencv，可使用该版本
用到的包:
imageio[pyav]
Pillow
"""
"""
import os
import imageio.v3 as iio
from PIL import Image

def save_image(image, folder, num):
    # 拼接图片完整路径，文件名为“00001.jpg”格式（五位数字）
    filename = str(num).zfill(5) + '.jpg'
    address = os.path.join(folder, filename)
    # 直接保存图片到指定路径，支持中文文件名
    Image.fromarray(image).save(address, quality=95)
    print('save image:', num, 'Picture name:', filename)

def main(input_video, start, timeF):
    # 获取视频所在的目录
    video_dir = os.path.dirname(input_video)
    # 定义保存图片的目录为视频所在目录下的 images 文件夹
    images_dir = os.path.join(video_dir, "images")
    # 如果 images 目录不存在，则创建
    if not os.path.exists(images_dir):
        os.makedirs(images_dir)

    # 读取视频流
    reader = iio.imiter(input_video, plugin="pyav")
    cnt = 0  # 计数器
    current_num = start

    # 按帧间隔保存图片
    for frame in reader:
        cnt += 1
        if cnt % timeF == 0:
            current_num += 1
            save_image(frame, images_dir, current_num)


if __name__ == '__main__':
    # 在下面修改输入视频路径、起始数字和每隔多少帧保存一张图片
    input_video = r"C:/Users/C:/Users/test.mp4"
    start = 0  # 文件名起始数字，不包括该数
    timeF = 10  # 每隔 timeF 帧保存一张图片
    main(input_video, start, timeF)

"""
