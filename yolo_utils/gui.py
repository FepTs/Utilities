"""Fast-starting Tk GUI with background execution and explicit confirmations."""

from __future__ import annotations

import json
import queue
import threading
import tkinter as tk
from dataclasses import dataclass
from tkinter import filedialog, messagebox, ttk
from typing import Callable

from . import __version__
from .common import UtilityError
from .converters import convert_json_folder_to_xml, convert_json_folder_to_yolo
from .dataset import format_split_report, split_dataset
from .files import compare_folders, delete_paths, matching_files, rename_files
from .labels import clean_labels, generate_empty_labels, generate_uniform_labels, merge_labels
from .video import extract_frames


@dataclass(frozen=True)
class Field:
    key: str
    label: str
    default: str = ""
    browse: str = ""
    choices: tuple[str, ...] = ()


@dataclass(frozen=True)
class Tool:
    name: str
    description: str
    fields: tuple[Field, ...]
    action: Callable[[dict[str, str]], str]
    destructive: bool = False


def _integer(values: dict[str, str], key: str, label: str) -> int:
    try:
        return int(values[key])
    except ValueError as error:
        raise UtilityError(f"{label}必须是整数。") from error


def _float(values: dict[str, str], key: str, label: str) -> float:
    try:
        return float(values[key])
    except ValueError as error:
        raise UtilityError(f"{label}必须是数字。") from error


def _split(values: dict[str, str]) -> str:
    report = split_dataset(
        values["input"],
        values["output"],
        _float(values, "ratio", "训练集比例"),
        values["task"],
        seed=_integer(values, "seed", "随机种子"),
    )
    return format_split_report(report)


def _compare(values: dict[str, str]) -> str:
    report = compare_folders(values["folder1"], values["folder2"])
    first = "\n".join(path.name for path in report.only_first) or "无"
    second = "\n".join(path.name for path in report.only_second) or "无"
    return (
        f"同名文件 {len(report.common)} 个。\n\n"
        f"仅文件夹 1（{len(report.only_first)}）：\n{first}\n\n"
        f"仅文件夹 2（{len(report.only_second)}）：\n{second}"
    )


def _delete(values: dict[str, str]) -> str:
    files = matching_files(values["folder"], values["feature"], values["extension"])
    if not files:
        return "没有匹配文件。"
    count = delete_paths(files)
    return f"已删除 {count} 个文件。"


def _rename(values: dict[str, str]) -> str:
    changes = rename_files(
        values["folder"],
        values["extension"],
        _integer(values, "start", "起始编号"),
    )
    preview = "\n".join(f"{old} → {new}" for old, new in changes[:20])
    suffix = "\n…" if len(changes) > 20 else ""
    return f"已重命名 {len(changes)} 个文件。\n{preview}{suffix}"


def _json_yolo(values: dict[str, str]) -> str:
    try:
        mapping = json.loads(values["mapping"])
    except json.JSONDecodeError as error:
        raise UtilityError(f"类别映射不是有效 JSON：{error}") from error
    report = convert_json_folder_to_yolo(values["input"], values["output"], mapping)
    return f"已转换 {report.converted} 个 JSON，跳过 {report.skipped_shapes} 个无效标注。"


def _json_xml(values: dict[str, str]) -> str:
    report = convert_json_folder_to_xml(values["input"], values["output"])
    return f"已转换 {report.converted} 个 JSON。"


def _generate(values: dict[str, str]) -> str:
    report = generate_uniform_labels(values["images"], values["output"], values["content"])
    return f"已生成 {report.changed} 个标签。"


def _empty(values: dict[str, str]) -> str:
    report = generate_empty_labels(values["images"], values["labels"])
    return f"已补齐 {report.changed} 个空标签。"


def _clean(values: dict[str, str]) -> str:
    try:
        classes = [int(item.strip()) for item in values["classes"].split(",") if item.strip()]
    except ValueError as error:
        raise UtilityError("类别必须是逗号分隔的整数。") from error
    report = clean_labels(values["labels"], classes)
    return f"已检查 {report.processed} 个标签，改写 {report.changed} 个。"


def _merge(values: dict[str, str]) -> str:
    report = merge_labels(values["target"], values["source"])
    return f"已合并 {report.changed} 个标签。"


def _video(values: dict[str, str]) -> str:
    report = extract_frames(
        values["input"],
        _integer(values, "start", "起始编号"),
        _integer(values, "interval", "帧间隔"),
        values["output"] or None,
    )
    return f"已通过 {report.backend} 提取 {report.extracted_count} 张图片。\n{report.output_folder}"


TOOLS = (
    Tool(
        "数据集划分",
        "按样本对随机划分；图片和同名标签始终一起移动。输出含可复现清单。",
        (
            Field("input", "输入数据集", browse="dir"),
            Field("output", "空输出目录", browse="dir"),
            Field("ratio", "训练集比例", "0.8"),
            Field("task", "任务类型", "detection", choices=("detection", "classification")),
            Field("seed", "随机种子", "42"),
        ),
        _split,
    ),
    Tool(
        "目录对比",
        "按文件主名比较图片和标签目录，不会修改文件。",
        (Field("folder1", "文件夹 1", browse="dir"), Field("folder2", "文件夹 2", browse="dir")),
        _compare,
    ),
    Tool(
        "JSON 转 YOLO",
        "将 LabelMe 矩形标注转换为规范化 YOLO 标签。",
        (
            Field("input", "JSON 目录", browse="dir"),
            Field("output", "标签输出目录", browse="dir"),
            Field("mapping", "类别映射", '{"car": 0}'),
        ),
        _json_yolo,
    ),
    Tool(
        "JSON 转 XML",
        "使用标准库转换 JSON，不再依赖 dicttoxml。",
        (Field("input", "JSON 目录", browse="dir"), Field("output", "XML 输出目录", browse="dir")),
        _json_xml,
    ),
    Tool(
        "生成统一标签",
        "为图片批量生成相同的测试标签。",
        (
            Field("images", "图片目录", browse="dir"),
            Field("output", "标签输出目录", browse="dir"),
            Field("content", "标签内容", "0 0.5 0.5 1.0 1.0"),
        ),
        _generate,
    ),
    Tool(
        "补齐空标签",
        "为没有同名标签的图片创建空 .txt 文件，不覆盖已有标签。",
        (Field("images", "图片目录", browse="dir"), Field("labels", "标签目录", browse="dir")),
        _empty,
    ),
    Tool(
        "清洗标签",
        "仅保留指定类别，并重新映射为从 0 开始的连续编号。",
        (Field("labels", "标签目录", browse="dir"), Field("classes", "保留类别", "0,1")),
        _clean,
        destructive=True,
    ),
    Tool(
        "合并标签",
        "把来源目录中的同名标签追加到目标标签，写入采用原子替换。",
        (
            Field("target", "目标标签目录", browse="dir"),
            Field("source", "来源标签目录", browse="dir"),
        ),
        _merge,
        destructive=True,
    ),
    Tool(
        "安全重命名",
        "使用两阶段重命名避免覆盖和名称碰撞。",
        (
            Field("folder", "文件夹", browse="dir"),
            Field("extension", "后缀（或 all）", "all"),
            Field("start", "起始编号", "1"),
        ),
        _rename,
        destructive=True,
    ),
    Tool(
        "批量删除",
        "删除文件名包含特征且后缀匹配的文件。",
        (
            Field("folder", "文件夹", browse="dir"),
            Field("feature", "文件名特征"),
            Field("extension", "后缀（可留空）"),
        ),
        _delete,
        destructive=True,
    ),
    Tool(
        "视频抽帧",
        "按需调用系统 FFmpeg；不捆绑 OpenCV，因此基础程序更轻、更快。",
        (
            Field("input", "视频文件", browse="file"),
            Field("output", "输出目录（可留空）", browse="dir"),
            Field("interval", "帧间隔", "10"),
            Field("start", "起始编号", "0"),
        ),
        _video,
    ),
)


class Application(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(f"YOLO Utilities {__version__}")
        self.geometry("880x620")
        self.minsize(760, 520)
        self._result_queue: queue.Queue[tuple[bool, str]] = queue.Queue()
        self._field_widgets: dict[str, tk.Widget] = {}
        self._tools = {tool.name: tool for tool in TOOLS}
        self._current = TOOLS[0]
        self._busy = False
        self._build_style()
        self._build_layout()
        self._select_tool(self._current.name)
        self.protocol("WM_DELETE_WINDOW", self._close)

    def _build_style(self) -> None:
        style = ttk.Style(self)
        if "vista" in style.theme_names():
            style.theme_use("vista")
        style.configure("Title.TLabel", font=("Microsoft YaHei UI", 16, "bold"))
        style.configure("Hint.TLabel", foreground="#4b5563")
        style.configure("Run.TButton", font=("Microsoft YaHei UI", 10, "bold"))

    def _build_layout(self) -> None:
        root = ttk.Frame(self, padding=16)
        root.pack(fill="both", expand=True)
        root.columnconfigure(1, weight=1)
        root.rowconfigure(1, weight=1)
        ttk.Label(root, text="YOLO 数据集工具箱", style="Title.TLabel").grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 12)
        )
        self.tool_list = tk.Listbox(
            root, width=20, borderwidth=0, highlightthickness=1, exportselection=False
        )
        for tool in TOOLS:
            self.tool_list.insert("end", tool.name)
        self.tool_list.grid(row=1, column=0, sticky="ns", padx=(0, 16))
        self.tool_list.bind("<<ListboxSelect>>", self._on_select)

        content = ttk.Frame(root)
        content.grid(row=1, column=1, sticky="nsew")
        content.columnconfigure(0, weight=1)
        content.rowconfigure(2, weight=1)
        self.description = ttk.Label(content, style="Hint.TLabel", wraplength=650)
        self.description.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        self.form = ttk.LabelFrame(content, text="参数", padding=12)
        self.form.grid(row=1, column=0, sticky="ew")
        self.form.columnconfigure(1, weight=1)
        self.output = tk.Text(content, height=13, wrap="word", state="disabled")
        self.output.grid(row=2, column=0, sticky="nsew", pady=(12, 8))
        self.run_button = ttk.Button(content, text="运行", style="Run.TButton", command=self._run)
        self.run_button.grid(row=3, column=0, sticky="e")

    def _on_select(self, _event: object) -> None:
        selection = self.tool_list.curselection()
        if selection:
            self._select_tool(self.tool_list.get(selection[0]))

    def _select_tool(self, name: str) -> None:
        self._current = self._tools[name]
        self.description.configure(text=self._current.description)
        for child in self.form.winfo_children():
            child.destroy()
        self._field_widgets.clear()
        for row, field in enumerate(self._current.fields):
            ttk.Label(self.form, text=field.label).grid(
                row=row, column=0, sticky="w", padx=(0, 10), pady=4
            )
            if field.choices:
                widget: tk.Widget = ttk.Combobox(self.form, values=field.choices, state="readonly")
                widget.set(field.default)
            else:
                widget = ttk.Entry(self.form)
                widget.insert(0, field.default)
            widget.grid(row=row, column=1, sticky="ew", pady=4)
            self._field_widgets[field.key] = widget
            if field.browse:
                ttk.Button(
                    self.form,
                    text="浏览…",
                    command=lambda item=field: self._browse(item),
                ).grid(row=row, column=2, padx=(8, 0), pady=4)
        self._set_output("准备就绪。")

    def _browse(self, field: Field) -> None:
        if field.browse == "file":
            selected = filedialog.askopenfilename(parent=self)
        else:
            selected = filedialog.askdirectory(parent=self)
        if selected:
            widget = self._field_widgets[field.key]
            widget.delete(0, "end")  # type: ignore[attr-defined]
            widget.insert(0, selected)  # type: ignore[attr-defined]

    def _values(self) -> dict[str, str]:
        return {
            key: str(widget.get()).strip()  # type: ignore[attr-defined]
            for key, widget in self._field_widgets.items()
        }

    def _run(self) -> None:
        values = self._values()
        required = [
            field.label
            for field in self._current.fields
            if not values[field.key] and "可留空" not in field.label
        ]
        if required:
            messagebox.showwarning("缺少参数", f"请填写：{'、'.join(required)}", parent=self)
            return
        if self._current.destructive and not messagebox.askyesno(
            "确认修改",
            f"“{self._current.name}”会修改或删除文件，确定继续吗？",
            icon="warning",
            parent=self,
        ):
            return
        self.run_button.configure(state="disabled")
        self._busy = True
        self._set_output("正在执行…")
        threading.Thread(target=self._execute, args=(self._current, values), daemon=True).start()
        self.after(80, self._poll_result)

    def _execute(self, tool: Tool, values: dict[str, str]) -> None:
        try:
            self._result_queue.put((True, tool.action(values)))
        except (UtilityError, OSError, json.JSONDecodeError) as error:
            self._result_queue.put((False, str(error)))
        except Exception as error:  # keep the GUI alive; unexpected failures are visible
            self._result_queue.put((False, f"未预期错误：{type(error).__name__}: {error}"))

    def _poll_result(self) -> None:
        try:
            success, message = self._result_queue.get_nowait()
        except queue.Empty:
            self.after(80, self._poll_result)
            return
        self.run_button.configure(state="normal")
        self._busy = False
        self._set_output(message)
        if not success:
            messagebox.showerror("执行失败", message, parent=self)

    def _close(self) -> None:
        if self._busy:
            messagebox.showwarning(
                "任务正在执行",
                "请等待当前任务完成后再关闭程序，避免中断文件操作。",
                parent=self,
            )
            return
        self.destroy()

    def _set_output(self, message: str) -> None:
        self.output.configure(state="normal")
        self.output.delete("1.0", "end")
        self.output.insert("1.0", message)
        self.output.configure(state="disabled")


def run() -> None:
    Application().mainloop()
