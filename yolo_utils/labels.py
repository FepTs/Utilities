"""YOLO label generation, cleaning, and merging."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .common import (
    IMAGE_SUFFIXES,
    UtilityError,
    atomic_write_text,
    index_unique_stems,
    require_directory,
    visible_files,
)


@dataclass(frozen=True)
class LabelOperationReport:
    processed: int
    changed: int
    details: tuple[str, ...] = ()


def _normalize_label_content(content: str) -> str:
    stripped = content.strip()
    if not stripped:
        raise UtilityError("标签内容不能为空。")
    _validate_yolo_line(stripped, source="标签内容")
    return stripped + "\n"


def _validate_yolo_line(line: str, *, source: str) -> tuple[int, list[str]]:
    parts = line.split()
    if len(parts) != 5:
        raise UtilityError(f"{source} 不是有效 YOLO 标注：每行必须有 5 个字段。")
    try:
        class_id = int(parts[0])
        coordinates = [float(value) for value in parts[1:]]
    except ValueError as error:
        raise UtilityError(f"{source} 包含非数字字段。") from error
    if class_id < 0:
        raise UtilityError(f"{source} 的类别编号不能为负数。")
    if any(not 0.0 <= value <= 1.0 for value in coordinates):
        raise UtilityError(f"{source} 的归一化坐标必须位于 0 到 1 之间。")
    return class_id, parts


def generate_uniform_labels(
    input_folder: str | Path, output_folder: str | Path, label_content: str
) -> LabelOperationReport:
    source = require_directory(input_folder, "图片目录")
    destination = Path(output_folder).expanduser().resolve()
    images = visible_files(source, IMAGE_SUFFIXES)
    if not images:
        raise UtilityError("图片目录中没有找到支持的图片。")
    content = _normalize_label_content(label_content)
    destination.mkdir(parents=True, exist_ok=True)
    for image in images:
        atomic_write_text(destination / f"{image.stem}.txt", content)
    return LabelOperationReport(len(images), len(images))


def generate_empty_labels(
    image_folder: str | Path, label_folder: str | Path
) -> LabelOperationReport:
    images_dir = require_directory(image_folder, "图片目录")
    labels_dir = Path(label_folder).expanduser().resolve()
    labels_dir.mkdir(parents=True, exist_ok=True)
    images = visible_files(images_dir, IMAGE_SUFFIXES)
    created: list[str] = []
    for image in images:
        target = labels_dir / f"{image.stem}.txt"
        if not target.exists():
            target.touch(exist_ok=False)
            created.append(target.name)
    return LabelOperationReport(len(images), len(created), tuple(created))


def clean_labels(
    folder_path: str | Path, valid_classes: list[int] | tuple[int, ...]
) -> LabelOperationReport:
    folder = require_directory(folder_path, "标签目录")
    try:
        classes = sorted({int(value) for value in valid_classes})
    except (TypeError, ValueError) as error:
        raise UtilityError("保留类别必须是整数列表。") from error
    if not classes or classes[0] < 0:
        raise UtilityError("至少需要一个非负类别编号。")
    mapping = {original: new for new, original in enumerate(classes)}

    labels = visible_files(folder, {".txt"})
    changed_files: list[str] = []
    prepared: list[tuple[Path, str]] = []
    for label_path in labels:
        original = label_path.read_text(encoding="utf-8-sig")
        output_lines: list[str] = []
        for line_number, raw_line in enumerate(original.splitlines(), start=1):
            stripped = raw_line.strip()
            if not stripped:
                continue
            class_id, parts = _validate_yolo_line(
                stripped, source=f"{label_path.name} 第 {line_number} 行"
            )
            if class_id in mapping:
                output_lines.append(" ".join([str(mapping[class_id]), *parts[1:]]))
        output = "\n".join(output_lines)
        if output:
            output += "\n"
        prepared.append((label_path, output))
        if output != original.replace("\r\n", "\n"):
            changed_files.append(label_path.name)

    # Validate every file before writing any of them.
    changed_set = set(changed_files)
    for label_path, output in prepared:
        if label_path.name in changed_set:
            atomic_write_text(label_path, output)
    return LabelOperationReport(len(labels), len(changed_files), tuple(changed_files))


def merge_labels(folder1: str | Path, folder2: str | Path) -> LabelOperationReport:
    destination = require_directory(folder1, "目标标签目录")
    source = require_directory(folder2, "待合并标签目录")
    target_files = index_unique_stems(visible_files(destination, {".txt"}), "目标标签目录")
    source_files = index_unique_stems(visible_files(source, {".txt"}), "待合并标签目录")
    merged: list[str] = []
    prepared: list[tuple[Path, str]] = []
    for key in sorted(target_files.keys() & source_files.keys()):
        target_path = target_files[key]
        addition = source_files[key].read_text(encoding="utf-8-sig").strip()
        if not addition:
            continue
        for line_number, line in enumerate(addition.splitlines(), start=1):
            _validate_yolo_line(
                line.strip(), source=f"{source_files[key].name} 第 {line_number} 行"
            )
        original = target_path.read_text(encoding="utf-8-sig").rstrip()
        for line_number, line in enumerate(original.splitlines(), start=1):
            _validate_yolo_line(line.strip(), source=f"{target_path.name} 第 {line_number} 行")
        combined = f"{original}\n{addition}\n" if original else f"{addition}\n"
        prepared.append((target_path, combined))
        merged.append(target_path.name)
    for target_path, content in prepared:
        atomic_write_text(target_path, content)
    return LabelOperationReport(
        len(target_files.keys() & source_files.keys()), len(merged), tuple(merged)
    )
