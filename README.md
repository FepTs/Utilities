# YOLO 数据集工具箱 🛠️

轻量级YOLO数据集处理工具箱 | 图形界面操作 | 支持简单的数据清洗/json格式转换

[![PyQt5](https://img.shields.io/badge/PyQt5-5.15%2B-green)](https://pypi.org/project/PyQt5/)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.5%2B-blue)](https://opencv.org/)

## 主要功能

### 🗑️ 数据处理
- **批量删除**   : 按文件名特征（例如`*`、`()`等）删除文件
- **目录比对**   : 校验两个文件夹文件一致性，支持一键删除
- **视频转图片** : 抽帧取图（已修复中文路径无法保存问题）
- **一键重命名** : 格式化文件名（五位数字编号）
- **数据集分割** : 适用于图像分割数据集，按比例随机划分train/val

### 🔄 格式转换
- `json → txt`  : 生成YOLO标准标签（支持两个版本）
- `json → xml`  : 转换为Pascal VOC格式
- **自动标签**  : 快速生成测试用统一标签（`.txt`）


## 快速开始
```bash
# 安装依赖
pip install -r requirements.txt
```
#### 若不想使用图形化界面，也可以直接使用`src`目录下各功能模块

****
本人训练数据集时常用的小工具，集成起来方便使用，同时也能练练手。后续可能会添加新功能。希望能帮到你！
