"""LabelMe JSON conversion using only the Python standard library."""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .common import UtilityError, atomic_write_text, require_directory, visible_files


@dataclass(frozen=True)
class ConversionReport:
    converted: int
    skipped_shapes: int = 0
    warnings: tuple[str, ...] = ()


def _read_json(path: Path) -> dict[str, Any]:
    last_error: Exception | None = None
    for encoding in ("utf-8-sig", "gb18030"):
        try:
            with path.open("r", encoding=encoding) as stream:
                payload = json.load(stream)
            if not isinstance(payload, dict):
                raise UtilityError(f"{path.name} 的顶层 JSON 必须是对象。")
            return payload
        except UnicodeDecodeError as error:
            last_error = error
    raise UtilityError(f"无法解码 JSON 文件：{path}") from last_error


def _normalize_mapping(label_mapping: dict[str, int]) -> dict[str, int]:
    if not isinstance(label_mapping, dict) or not label_mapping:
        raise UtilityError('类别映射必须是非空对象，例如 {"car": 0}。')
    if any(isinstance(class_id, bool) for class_id in label_mapping.values()):
        raise UtilityError("类别编号必须是整数，不能使用布尔值。")
    try:
        normalized = {str(name): int(class_id) for name, class_id in label_mapping.items()}
    except (TypeError, ValueError) as error:
        raise UtilityError("类别映射的值必须是整数。") from error
    if any(class_id < 0 for class_id in normalized.values()):
        raise UtilityError("类别编号不能为负数。")
    if len(set(normalized.values())) != len(normalized):
        raise UtilityError("不同类别不能映射到同一个编号。")
    return normalized


def convert_json_to_yolo(
    json_path: str | Path, output_path: str | Path, label_mapping: dict[str, int]
) -> tuple[int, tuple[str, ...]]:
    source = Path(json_path).expanduser().resolve()
    if not source.is_file():
        raise UtilityError(f"JSON 文件不存在：{source}")
    mapping = _normalize_mapping(label_mapping)
    data = _read_json(source)
    try:
        width = float(data["imageWidth"])
        height = float(data["imageHeight"])
    except (KeyError, TypeError, ValueError) as error:
        raise UtilityError(f"{source.name} 缺少有效的 imageWidth/imageHeight。") from error
    if width <= 0 or height <= 0:
        raise UtilityError(f"{source.name} 的图片尺寸必须大于 0。")

    lines: list[str] = []
    warnings: list[str] = []
    shapes = data.get("shapes", [])
    if not isinstance(shapes, list):
        raise UtilityError(f"{source.name} 的 shapes 必须是数组。")
    for index, shape in enumerate(shapes, start=1):
        if not isinstance(shape, dict) or shape.get("shape_type", "rectangle") != "rectangle":
            warnings.append(f"第 {index} 个标注不是矩形，已跳过。")
            continue
        label = str(shape.get("label", ""))
        if label not in mapping:
            warnings.append(f"第 {index} 个标注类别“{label}”未配置，已跳过。")
            continue
        points = shape.get("points")
        if (
            not isinstance(points, list)
            or len(points) < 2
            or any(not isinstance(point, list) or len(point) < 2 for point in points)
        ):
            warnings.append(f"第 {index} 个标注坐标无效，已跳过。")
            continue
        try:
            xs = [float(point[0]) for point in points]
            ys = [float(point[1]) for point in points]
        except (TypeError, ValueError):
            warnings.append(f"第 {index} 个标注坐标不是数字，已跳过。")
            continue
        x_min, x_max = max(0.0, min(xs)), min(width, max(xs))
        y_min, y_max = max(0.0, min(ys)), min(height, max(ys))
        if x_max <= x_min or y_max <= y_min:
            warnings.append(f"第 {index} 个标注面积为 0，已跳过。")
            continue
        values = (
            (x_min + x_max) / (2.0 * width),
            (y_min + y_max) / (2.0 * height),
            (x_max - x_min) / width,
            (y_max - y_min) / height,
        )
        lines.append(f"{mapping[label]} " + " ".join(f"{value:.6f}" for value in values))
    content = "\n".join(lines)
    if content:
        content += "\n"
    atomic_write_text(Path(output_path).expanduser().resolve(), content)
    return len(lines), tuple(warnings)


def convert_json_folder_to_yolo(
    input_folder: str | Path,
    output_folder: str | Path,
    label_mapping: dict[str, int],
) -> ConversionReport:
    source = require_directory(input_folder, "JSON 输入目录")
    destination = Path(output_folder).expanduser().resolve()
    files = visible_files(source, {".json"})
    if not files:
        raise UtilityError("输入目录中没有找到 JSON 文件。")
    destination.mkdir(parents=True, exist_ok=True)
    skipped = 0
    warnings: list[str] = []
    for json_file in files:
        _, file_warnings = convert_json_to_yolo(
            json_file, destination / f"{json_file.stem}.txt", label_mapping
        )
        skipped += len(file_warnings)
        warnings.extend(f"{json_file.name}: {warning}" for warning in file_warnings)
    return ConversionReport(len(files), skipped, tuple(warnings))


def _append_xml(parent: ET.Element, key: str, value: Any) -> None:
    if isinstance(value, dict):
        child = ET.SubElement(parent, key)
        for nested_key, nested_value in value.items():
            _append_xml(child, str(nested_key), nested_value)
    elif isinstance(value, list):
        child = ET.SubElement(parent, key)
        for item in value:
            _append_xml(child, "item", item)
    else:
        child = ET.SubElement(parent, key)
        child.text = "" if value is None else str(value)


def convert_json_to_xml(json_path: str | Path, xml_path: str | Path) -> None:
    source = Path(json_path).expanduser().resolve()
    data = _read_json(source)
    root = ET.Element("Annotations")
    for key, value in data.items():
        _append_xml(root, str(key), value)
    ET.indent(root, space="  ")
    xml = '<?xml version="1.0" encoding="utf-8"?>\n' + ET.tostring(root, encoding="unicode")
    atomic_write_text(Path(xml_path).expanduser().resolve(), xml + "\n")


def convert_json_folder_to_xml(
    input_folder: str | Path, output_folder: str | Path
) -> ConversionReport:
    source = require_directory(input_folder, "JSON 输入目录")
    destination = Path(output_folder).expanduser().resolve()
    files = visible_files(source, {".json"})
    if not files:
        raise UtilityError("输入目录中没有找到 JSON 文件。")
    destination.mkdir(parents=True, exist_ok=True)
    for json_file in files:
        convert_json_to_xml(json_file, destination / f"{json_file.stem}.xml")
    return ConversionReport(len(files))
