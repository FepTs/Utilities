# YOLO Utilities 2.0

轻量、易用、可靠的 YOLO 数据集工具箱。2.0 对旧项目进行了完整重构：默认运行时只使用
Python 标准库，图形界面由 Tk 提供，不再强制安装 PyQt5、OpenCV 和 `dicttoxml`。

## 这次升级解决了什么

- **修复数据集错配**：检测数据集先组成“图片 + 同名标签”的不可分割样本对，再只对样本对洗牌。
  图片和标签不会再各自随机划分。
- **结果可复现**：默认随机种子为 `42`，输出目录包含 `split_manifest.json`，记录每个样本所在集合。
- **避免半成品数据集**：先在同级临时目录完成全部复制，成功后一次性发布；复制失败会清理临时结果。
- **启动更快、打包更小**：移除 Qt 与 OpenCV 的基础依赖。视频抽帧仅在使用该功能时调用系统 FFmpeg。
- **文件操作更安全**：删除和改写操作需要明确确认；批量重命名采用两阶段算法，避免名称碰撞和覆盖。
- **写入更可靠**：标签清洗、合并和转换使用原子替换，避免异常中断造成文件截断。
- **修复历史问题**：模块导入不再生成文件；视频资源正确由 FFmpeg 管理；JSON 转 YOLO 修复旧版中心点
  `-1` 偏移；路径、比例、重复主名、无效标签和空数据集都有明确校验。
- **同时提供 GUI 和 CLI**：日常操作可用图形界面，批处理和 CI 可使用命令行。

## 快速开始

需要 Python 3.10 或更高版本。

```powershell
python main.py
```

基础功能没有第三方 Python 依赖，因此无需先执行 `pip install -r requirements.txt`。

也可以安装为命令行工具：

```powershell
python -m pip install .
yolo-utilities --help
yolo-utilities-gui
```

## 正确划分数据集

目标检测输入结构：

```text
dataset/
├── images/
│   ├── 001.jpg
│   └── 002.png
└── labels/
    ├── 001.txt
    └── 002.txt
```

图形界面选择“数据集划分”，或运行：

```powershell
yolo-utilities split dataset output --task detection --ratio 0.7 --seed 42
```

输出结构：

```text
output/
├── train/
│   ├── images/
│   └── labels/
├── val/
│   ├── images/
│   └── labels/
└── split_manifest.json
```

只有主文件名相同的图片和 `.txt` 标签会构成有效样本。无标签图片和孤立标签不会被静默混入，
其名称会写入划分报告与清单。同一目录中若有 `1.jpg` 和 `1.png` 这类重复主名，程序会停止并提示，
避免两个图片错误共用一个标签。

分类数据集使用 `--task classification`，输入目录中的每个子目录代表一个类别。

## 可用命令

```text
split             划分检测或分类数据集
compare           按文件主名比较两个目录
delete            按文件名特征和后缀删除（必须添加 --yes）
rename            安全批量重命名（必须添加 --yes）
json2yolo         LabelMe JSON 转 YOLO
json2xml          JSON 转 XML
generate-labels   批量生成相同标签
generate-empty    为缺少标签的图片补齐空标签
clean-labels      清洗并连续重映射类别（必须添加 --yes）
merge-labels      合并同名标签（必须添加 --yes）
video             使用 FFmpeg 按帧间隔抽图
```

查看任一命令的完整参数：

```powershell
yolo-utilities split --help
```

## 视频抽帧

视频功能不再让每位用户承担 OpenCV 与 NumPy 的安装、导入和打包体积。需要视频抽帧时，请安装
[FFmpeg](https://ffmpeg.org/) 并确保 `ffmpeg` 在 `PATH` 中：

```powershell
yolo-utilities video input.mp4 --interval 10 --start 0
```

默认输出到视频同级的 `images` 目录。

## 构建 Windows 单文件程序

```powershell
.\scripts\build.ps1
```

脚本会创建隔离的 `.venv-build` 环境，避免把本机科学计算包误打入程序。产物位于
`dist\YoloUtilities.exe`。CI 也会在每次提交和拉取请求中运行测试并构建 Windows 产物。

## 测试

```powershell
python -m unittest discover -s tests -v
python -m pip install -r requirements-dev.txt
python -m ruff check main.py yolo_utils src tests
python -m ruff format --check main.py yolo_utils src tests
```

旧的 `src/*.py` 导入路径仍保留为兼容层；新代码建议直接使用 `yolo_utils` 包。
