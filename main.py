"""
PyQt界面 v0.8 by FepTs

更新日志:
v0.8:修复comparefolders的bug，现在可以实时看到命令行的输出信息
v0.7:描述，提示更改，优化细节
v0.6:增加新的集成功能，大部分已有功能集成完毕
v0.5:增加新的集成功能，包内函数bug修复，rename功能加强，现在支持中文路径了
v0.3:增加新的集成功能，video2photo功能加强，框架重构，逻辑完善
v0.2:删除无法使用的旧输入面板，删除无法使用的功能，增加交互提示，更改界面布局
v0.1:仅集成了较少功能的初始测试版本
"""

import sys
import importlib
import ast
import os
from PyQt5 import QtCore, QtWidgets


class Worker(QtCore.QThread):
    """工作线程，用于执行工具函数并捕获输出"""
    output_signal = QtCore.pyqtSignal(str)
    error_signal = QtCore.pyqtSignal(str)
    finished_signal = QtCore.pyqtSignal()
    input_request_signal = QtCore.pyqtSignal(str)

    def __init__(self, func, args, kwargs=None):
        super(Worker, self).__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs if kwargs is not None else {}
        self.input_buffer = None
        self.input_ready = False
        self.current_prompt = None
        self.output_buffer = []

    def run(self):
        old_stdout = sys.stdout
        old_stdin = sys.stdin
        sys.stdout = self
        sys.stdin = self

        try:
            self.func(*self.args, **self.kwargs)
        except Exception as e:
            self.error_signal.emit("错误：" + str(e))
        finally:
            sys.stdout = old_stdout
            sys.stdin = old_stdin
        self.finished_signal.emit()

    def write(self, text):
        """重写write方法以实时显示输出"""
        if text.strip():  # 忽略空行
            self.output_signal.emit(text)
            # 如果输出包含提示信息，设置当前提示
            if "是否删除以上所有文件？" in text:
                self.current_prompt = text.strip()

    def flush(self):
        """实现flush方法"""
        pass

    def readline(self):
        """重写readline方法以支持输入请求"""
        if not self.current_prompt:
            self.current_prompt = "请输入(y/n): "
        self.input_request_signal.emit(self.current_prompt)
        while not self.input_ready:
            self.msleep(100)
        self.input_ready = False
        self.current_prompt = None
        return self.input_buffer + "\n"

    def write_input(self, text):
        """处理用户输入"""
        self.input_buffer = text
        self.input_ready = True


class BasePanel(QtWidgets.QWidget):
    """基础面板类，提供通用的文件/文件夹选择功能"""
    def __init__(self, parent=None):
        super(BasePanel, self).__init__(parent)
        self.layout = QtWidgets.QFormLayout()
        self.setLayout(self.layout)

    def add_file_selector(self, label, callback):
        """添加文件选择器"""
        line = QtWidgets.QLineEdit()
        btn = QtWidgets.QPushButton("浏览")
        btn.clicked.connect(lambda: self.browse_file(line, callback))
        h_layout = QtWidgets.QHBoxLayout()
        h_layout.addWidget(line)
        h_layout.addWidget(btn)
        self.layout.addRow(label, h_layout)
        return line

    def add_dir_selector(self, label, callback):
        """添加文件夹选择器"""
        line = QtWidgets.QLineEdit()
        btn = QtWidgets.QPushButton("浏览")
        btn.clicked.connect(lambda: self.browse_dir(line, callback))
        h_layout = QtWidgets.QHBoxLayout()
        h_layout.addWidget(line)
        h_layout.addWidget(btn)
        self.layout.addRow(label, h_layout)
        return line

    def browse_file(self, line_edit, callback):
        """浏览文件"""
        file_name, _ = QtWidgets.QFileDialog.getOpenFileName(self, "选择文件")
        if file_name:
            line_edit.setText(file_name)
            if callback:
                callback(file_name)

    def browse_dir(self, line_edit, callback):
        """浏览文件夹"""
        dir_name = QtWidgets.QFileDialog.getExistingDirectory(self, "选择文件夹")
        if dir_name:
            line_edit.setText(dir_name)
            if callback:
                callback(dir_name)


class Video2PhotoPanel(BasePanel):
    """视频转图片功能面板"""
    def __init__(self, parent=None):
        super(Video2PhotoPanel, self).__init__(parent)
        self.inputLine = self.add_file_selector("视频文件路径:", None)
        self.startLine = QtWidgets.QLineEdit()
        self.startLine.setPlaceholderText("整数，例如：0")
        self.layout.addRow("起始编号:", self.startLine)
        self.timeFLine = QtWidgets.QLineEdit()
        self.timeFLine.setPlaceholderText("整数，例如：5")
        self.layout.addRow("帧间隔:", self.timeFLine)


class Json2TxtPanel(BasePanel):
    """JSON转TXT功能面板（v1和v2共用）"""
    def __init__(self, parent=None):
        super(Json2TxtPanel, self).__init__(parent)
        self.inputDirLine = self.add_dir_selector("输入文件夹路径:", None)
        self.outputDirLine = self.add_dir_selector("输出文件夹路径:", None)
        self.mapLine = QtWidgets.QLineEdit()
        self.mapLine.setPlaceholderText('例如: {"car":0, "line":1}')
        self.layout.addRow("类别映射:", self.mapLine)


class CompareFoldersPanel(BasePanel):
    """比较文件夹功能面板"""
    def __init__(self, parent=None):
        super(CompareFoldersPanel, self).__init__(parent)
        self.folder1Line = self.add_dir_selector("文件夹1路径:", None)
        self.folder2Line = self.add_dir_selector("文件夹2路径:", None)


class DatasetSplitPanel(BasePanel):
    """数据集分割功能面板"""
    def __init__(self, parent=None):
        super(DatasetSplitPanel, self).__init__(parent)
        self.inputDirLine = self.add_dir_selector("原始数据集路径:", None)
        self.outputDirLine = self.add_dir_selector("输出数据集路径:", None)
        self.ratioLine = QtWidgets.QLineEdit()
        self.ratioLine.setPlaceholderText("0.0-1.0，例如：0.8")
        self.layout.addRow("训练集比例:", self.ratioLine)


class GenerationLabelsPanel(BasePanel):
    """生成标签功能面板"""
    def __init__(self, parent=None):
        super(GenerationLabelsPanel, self).__init__(parent)
        self.inputDirLine = self.add_dir_selector("图片文件夹路径:", None)
        self.outputDirLine = self.add_dir_selector("标签输出路径:", None)
        self.labelContentLine = QtWidgets.QLineEdit()
        self.labelContentLine.setPlaceholderText('例如: 0 0.503846 0.515625 0.992308 0.968750')
        self.layout.addRow("标签内容:", self.labelContentLine)


class BatchDeletionPanel(BasePanel):
    """批量删除功能面板"""
    def __init__(self, parent=None):
        super(BatchDeletionPanel, self).__init__(parent)
        self.inputDirLine = self.add_dir_selector("文件夹路径:", None)
        self.featureLine = QtWidgets.QLineEdit()
        self.featureLine.setPlaceholderText("例如: train, *, ()")
        self.layout.addRow("文件名特征:", self.featureLine)
        self.extensionLine = QtWidgets.QLineEdit()
        self.extensionLine.setPlaceholderText("例如: .txt, .jpg")
        self.layout.addRow("文件后缀:", self.extensionLine)


class RenamePanel(BasePanel):
    """批量重命名功能面板"""
    def __init__(self, parent=None):
        super(RenamePanel, self).__init__(parent)
        self.inputDirLine = self.add_dir_selector("文件夹路径:", None)
        self.extensionLine = QtWidgets.QLineEdit()
        self.extensionLine.setPlaceholderText("例如: jpg, png (输入all处理所有文件)")
        self.layout.addRow("文件后缀:", self.extensionLine)
        self.startNumberLine = QtWidgets.QLineEdit()
        self.startNumberLine.setPlaceholderText("整数，例如：1")
        self.layout.addRow("起始编号:", self.startNumberLine)


class MainWindow(QtWidgets.QWidget):
    """主窗口"""
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setWindowTitle("YoloUtilities-v0.8")
        self.resize(800, 600)
        self.init_ui()

    def init_ui(self):
        main_layout = QtWidgets.QVBoxLayout()

        # 功能选择按钮区域
        button_layout = QtWidgets.QHBoxLayout()
        self.function_buttons = []
        functions = [
            ("Video2Photo", "视频转图片"),
            ("Json2TxtV1", "JSON转TXT(v1)"),
            ("Json2TxtV2", "JSON转TXT(v2)"),
            ("CompareFolders", "比较文件夹"),
            ("DatasetSplit", "数据集分割"),
            ("GenerationLabels", "生成标签"),
            ("BatchDeletion", "批量删除"),
            ("Rename", "批量重命名")
        ]
        
        for func_name, display_name in functions:
            btn = QtWidgets.QPushButton(display_name)
            btn.clicked.connect(lambda checked, name=func_name: self.switch_function(name))
            button_layout.addWidget(btn)
            self.function_buttons.append(btn)
        
        main_layout.addLayout(button_layout)

        # 功能描述显示区
        self.description_label = QtWidgets.QLabel("请在上方选择功能\n使用对应功能前，请确保所需的库已安装\n警告：删除操作无法撤销，请再三核对参数后谨慎使用！！!")
        self.description_label.setWordWrap(True)
        main_layout.addWidget(self.description_label)

        # 输入控件区域
        self.stacked_widget = QtWidgets.QStackedWidget()
        self.panels = {
            "Video2Photo": Video2PhotoPanel(),
            "Json2TxtV1": Json2TxtPanel(),
            "Json2TxtV2": Json2TxtPanel(),
            "CompareFolders": CompareFoldersPanel(),
            "DatasetSplit": DatasetSplitPanel(),
            "GenerationLabels": GenerationLabelsPanel(),
            "BatchDeletion": BatchDeletionPanel(),
            "Rename": RenamePanel()
        }
        
        for panel in self.panels.values():
            self.stacked_widget.addWidget(panel)
        
        main_layout.addWidget(self.stacked_widget)

        # 运行按钮
        self.run_button = QtWidgets.QPushButton("运行")
        self.run_button.clicked.connect(self.run_current_function)
        main_layout.addWidget(self.run_button)

        # 输出显示区
        self.output_text = QtWidgets.QTextEdit()
        self.output_text.setReadOnly(True)
        main_layout.addWidget(self.output_text)

        # 用户输入区域
        input_layout = QtWidgets.QHBoxLayout()
        self.input_line = QtWidgets.QLineEdit()
        self.input_line.setPlaceholderText("在此输入...")
        self.input_button = QtWidgets.QPushButton("确认")
        self.input_button.clicked.connect(self.handle_user_input)
        self.input_button.setEnabled(False)
        self.input_line.setEnabled(False)
        input_layout.addWidget(self.input_line)
        input_layout.addWidget(self.input_button)
        main_layout.addLayout(input_layout)

        self.setLayout(main_layout)

        # 功能描述
        self.descriptions = {
            "Video2Photo": "【视频转图片功能】\n读取视频文件，每隔一定帧数提取一帧图片并保存。\n参数：\n- 视频文件路径\n- 起始编号（不包括该数）\n- 帧间隔",
            "Json2TxtV1": "【JSON转TXT功能(v1)】\n将输入文件夹中的JSON文件转换为TXT格式。（简化的json版本，如labelme）\n参数：\n- 输入文件夹路径\n- 输出文件夹路径\n- 类别映射",
            "Json2TxtV2": "【JSON转TXT功能(v2)】\n将输入文件夹中的JSON文件转换为TXT格式。（通用json版本）\n参数：\n- 输入文件夹路径\n- 输出文件夹路径\n- 类别映射",
            "CompareFolders": "【比较文件夹功能】\n比较两个目录中文件名是否相同，可以用于检验标签文件或图像的丢失。\n支持一键删除多余文件\n参数：\n- 文件夹1路径\n- 文件夹2路径",
            "DatasetSplit": "【数据集分割功能】\n用于图像分割数据集的制作，将数据集划分为训练集和验证集。\n参数：\n- 原始数据集路径\n- 输出数据集路径\n- 训练集比例",
            "GenerationLabels": "【生成标签功能】\n用于给所有图片生成相同测试标签。\n参数：\n- 图片文件夹路径\n- 标签输出路径\n- 标签内容",
            "BatchDeletion": "【批量删除功能】\n用于批量删除指定文件夹中包含特定字符特征的文件。\n参数：\n- 文件夹路径\n- 文件名特征（例如：train, *, ()）\n- 文件后缀（例如：.txt, .jpg）",
            "Rename": "【批量重命名功能】\n用于重命名文件夹中的文件，支持指定后缀或重命名所有文件。\n参数：\n- 文件夹路径\n- 文件后缀（例如：jpg, png，输入all处理所有文件）\n- 起始编号"
        }

        # 初始化工作线程
        self.worker = None

    def switch_function(self, function_name):
        """切换功能面板"""
        self.stacked_widget.setCurrentWidget(self.panels[function_name])
        self.description_label.setText(self.descriptions.get(function_name, ""))
        self.output_text.clear()

    def handle_user_input(self):
        """处理用户输入"""
        if self.worker:
            text = self.input_line.text()
            self.worker.write_input(text)
            self.input_line.clear()
            self.input_button.setEnabled(False)
            self.input_line.setEnabled(False)

    def run_current_function(self):
        """运行当前选中的功能"""
        current_panel = self.stacked_widget.currentWidget()
        function_name = None
        for name, panel in self.panels.items():
            if panel == current_panel:
                function_name = name
                break

        if not function_name:
            return

        try:
            if function_name == "Video2Photo":
                video_file = self.panels["Video2Photo"].inputLine.text().strip()
                start_str = self.panels["Video2Photo"].startLine.text().strip()
                timeF_str = self.panels["Video2Photo"].timeFLine.text().strip()
                if not video_file or not start_str or not timeF_str:
                    QtWidgets.QMessageBox.warning(self, "警告", "请填写所有参数！")
                    return
                start = int(start_str)
                timeF = int(timeF_str)
                module = importlib.import_module("src.Video2Photo")
                func = module.main
                args = (video_file, start, timeF)

            elif function_name in ["Json2TxtV1", "Json2TxtV2"]:
                input_dir = self.panels[function_name].inputDirLine.text().strip()
                output_dir = self.panels[function_name].outputDirLine.text().strip()
                map_str = self.panels[function_name].mapLine.text().strip()
                if not input_dir or not output_dir or not map_str:
                    QtWidgets.QMessageBox.warning(self, "警告", "请填写所有参数！")
                    return
                try:
                    label_map = ast.literal_eval(map_str)
                except Exception:
                    QtWidgets.QMessageBox.warning(self, "警告", "类别映射格式错误！")
                    return
                module = importlib.import_module(f"src.{function_name.lower()}")
                func = module.main
                args = (input_dir, output_dir, label_map)

            elif function_name == "CompareFolders":
                folder1 = self.panels["CompareFolders"].folder1Line.text().strip()
                folder2 = self.panels["CompareFolders"].folder2Line.text().strip()
                if not folder1 or not folder2:
                    QtWidgets.QMessageBox.warning(self, "警告", "请填写所有参数！")
                    return
                module = importlib.import_module("src.CompareFolders")
                func = module.main
                args = (folder1, folder2)

            elif function_name == "DatasetSplit":
                input_dir = self.panels["DatasetSplit"].inputDirLine.text().strip()
                output_dir = self.panels["DatasetSplit"].outputDirLine.text().strip()
                ratio_str = self.panels["DatasetSplit"].ratioLine.text().strip()
                if not input_dir or not output_dir or not ratio_str:
                    QtWidgets.QMessageBox.warning(self, "警告", "请填写所有参数！")
                    return
                try:
                    ratio = float(ratio_str)
                    if not 0 <= ratio <= 1:
                        raise ValueError
                except ValueError:
                    QtWidgets.QMessageBox.warning(self, "警告", "训练集比例必须在0到1之间！")
                    return
                module = importlib.import_module("src.DatasetSplit")
                func = module.main
                args = (input_dir, output_dir, ratio)

            elif function_name == "GenerationLabels":
                input_dir = self.panels["GenerationLabels"].inputDirLine.text().strip()
                output_dir = self.panels["GenerationLabels"].outputDirLine.text().strip()
                label_content = self.panels["GenerationLabels"].labelContentLine.text().strip()
                if not input_dir or not output_dir or not label_content:
                    QtWidgets.QMessageBox.warning(self, "警告", "请填写所有参数！")
                    return
                module = importlib.import_module("src.GenerationLabels")
                func = module.main
                args = (input_dir, output_dir, label_content)

            elif function_name == "BatchDeletion":
                input_dir = self.panels["BatchDeletion"].inputDirLine.text().strip()
                feature = self.panels["BatchDeletion"].featureLine.text().strip()
                extension = self.panels["BatchDeletion"].extensionLine.text().strip()
                if not input_dir or not feature or not extension:
                    QtWidgets.QMessageBox.warning(self, "警告", "请填写所有参数！")
                    return
                module = importlib.import_module("src.BatchDeletion")
                func = module.main
                args = (input_dir, feature, extension)

            elif function_name == "Rename":
                input_dir = self.panels["Rename"].inputDirLine.text().strip()
                extension = self.panels["Rename"].extensionLine.text().strip()
                start_number_str = self.panels["Rename"].startNumberLine.text().strip()
                if not input_dir or not extension or not start_number_str:
                    QtWidgets.QMessageBox.warning(self, "警告", "请填写所有参数！")
                    return
                try:
                    start_number = int(start_number_str)
                    if start_number < 0:
                        raise ValueError
                except ValueError:
                    QtWidgets.QMessageBox.warning(self, "警告", "起始编号必须是非负整数！")
                    return
                module = importlib.import_module("src.Rename")
                func = module.main
                args = (input_dir, extension, start_number)

            self.output_text.append("开始执行...\n")
            self.worker = Worker(func, args)
            self.worker.output_signal.connect(self.append_output)
            self.worker.error_signal.connect(self.append_output)
            self.worker.input_request_signal.connect(self.handle_input_request)
            self.worker.finished_signal.connect(self.handle_finished)
            self.worker.start()

        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "错误", str(e))

    def append_output(self, text):
        """添加输出文本"""
        self.output_text.append(text)

    def handle_input_request(self, prompt):
        """处理输入请求"""
        # 不再重复显示提示，因为已经在输出区域显示了
        self.input_line.setEnabled(True)
        self.input_button.setEnabled(True)
        self.input_line.setFocus()

    def handle_finished(self):
        """处理执行完成"""
        self.output_text.append("\n执行完毕.")
        self.input_line.setEnabled(False)
        self.input_button.setEnabled(False)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
