"""Command-line interface for automation and headless use."""

from __future__ import annotations

import argparse
import json
import sys

from . import __version__
from .common import UtilityError
from .converters import convert_json_folder_to_xml, convert_json_folder_to_yolo
from .dataset import format_split_report, split_dataset
from .files import compare_folders, delete_paths, matching_files, rename_files
from .labels import clean_labels, generate_empty_labels, generate_uniform_labels, merge_labels
from .video import extract_frames


def _mapping(value: str) -> dict[str, int]:
    try:
        result = json.loads(value)
    except json.JSONDecodeError as error:
        raise argparse.ArgumentTypeError(f"不是有效 JSON：{error}") from error
    if not isinstance(result, dict):
        raise argparse.ArgumentTypeError("类别映射必须是 JSON 对象。")
    return result


def _classes(value: str) -> list[int]:
    try:
        return [int(item.strip()) for item in value.split(",") if item.strip()]
    except ValueError as error:
        raise argparse.ArgumentTypeError("类别应为逗号分隔的整数。") from error


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="yolo-utilities", description="轻量、可靠的 YOLO 数据集工具箱"
    )
    parser.add_argument("--version", action="version", version=__version__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    split = subparsers.add_parser("split", help="划分检测或分类数据集")
    split.add_argument("input")
    split.add_argument("output")
    split.add_argument("--ratio", type=float, default=0.8)
    split.add_argument("--task", choices=("detection", "classification"), default="detection")
    split.add_argument("--seed", type=int, default=42)

    compare = subparsers.add_parser("compare", help="按文件主名比较两个目录")
    compare.add_argument("folder1")
    compare.add_argument("folder2")

    delete = subparsers.add_parser("delete", help="批量删除匹配文件")
    delete.add_argument("folder")
    delete.add_argument("feature")
    delete.add_argument("--extension", default="")
    delete.add_argument("--yes", action="store_true", help="确认执行删除")

    rename = subparsers.add_parser("rename", help="安全批量重命名")
    rename.add_argument("folder")
    rename.add_argument("--extension", default="all")
    rename.add_argument("--start", type=int, default=1)
    rename.add_argument("--yes", action="store_true", help="确认执行重命名")

    json_yolo = subparsers.add_parser("json2yolo", help="LabelMe JSON 转 YOLO")
    json_yolo.add_argument("input")
    json_yolo.add_argument("output")
    json_yolo.add_argument("--mapping", type=_mapping, required=True)

    json_xml = subparsers.add_parser("json2xml", help="JSON 转 XML")
    json_xml.add_argument("input")
    json_xml.add_argument("output")

    uniform = subparsers.add_parser("generate-labels", help="批量生成相同标签")
    uniform.add_argument("images")
    uniform.add_argument("output")
    uniform.add_argument("--content", required=True)

    empty = subparsers.add_parser("generate-empty", help="补齐空标签")
    empty.add_argument("images")
    empty.add_argument("labels")

    clean = subparsers.add_parser("clean-labels", help="清洗并重映射标签类别")
    clean.add_argument("labels")
    clean.add_argument("--classes", type=_classes, required=True)
    clean.add_argument("--yes", action="store_true", help="确认改写标签")

    merge = subparsers.add_parser("merge-labels", help="合并同名标签")
    merge.add_argument("target")
    merge.add_argument("source")
    merge.add_argument("--yes", action="store_true", help="确认改写标签")

    video = subparsers.add_parser("video", help="使用 FFmpeg 按帧间隔抽图")
    video.add_argument("input")
    video.add_argument("--output")
    video.add_argument("--interval", type=int, default=10)
    video.add_argument("--start", type=int, default=0)
    return parser


def _require_confirmation(args: argparse.Namespace, action: str) -> None:
    if not args.yes:
        raise UtilityError(f"{action}会修改文件；确认后请添加 --yes。")


def run(args: argparse.Namespace) -> str:
    if args.command == "split":
        return format_split_report(
            split_dataset(args.input, args.output, args.ratio, args.task, seed=args.seed)
        )
    if args.command == "compare":
        report = compare_folders(args.folder1, args.folder2)
        first = "\n".join(f"  {path.name}" for path in report.only_first) or "  无"
        second = "\n".join(f"  {path.name}" for path in report.only_second) or "  无"
        return f"同名文件：{len(report.common)} 个\n仅文件夹 1：\n{first}\n仅文件夹 2：\n{second}"
    if args.command == "delete":
        matches = matching_files(args.folder, args.feature, args.extension)
        if not matches:
            return "没有匹配文件。"
        _require_confirmation(args, "删除")
        return f"已删除 {delete_paths(matches)} 个文件。"
    if args.command == "rename":
        _require_confirmation(args, "重命名")
        changes = rename_files(args.folder, args.extension, args.start)
        return f"已重命名 {len(changes)} 个文件。"
    if args.command == "json2yolo":
        report = convert_json_folder_to_yolo(args.input, args.output, args.mapping)
        return f"已转换 {report.converted} 个 JSON；跳过 {report.skipped_shapes} 个无效标注。"
    if args.command == "json2xml":
        report = convert_json_folder_to_xml(args.input, args.output)
        return f"已转换 {report.converted} 个 JSON。"
    if args.command == "generate-labels":
        report = generate_uniform_labels(args.images, args.output, args.content)
        return f"已生成 {report.changed} 个标签。"
    if args.command == "generate-empty":
        report = generate_empty_labels(args.images, args.labels)
        return f"已补齐 {report.changed} 个空标签。"
    if args.command == "clean-labels":
        _require_confirmation(args, "标签清洗")
        report = clean_labels(args.labels, args.classes)
        return f"已检查 {report.processed} 个标签，改写 {report.changed} 个。"
    if args.command == "merge-labels":
        _require_confirmation(args, "标签合并")
        report = merge_labels(args.target, args.source)
        return f"已合并 {report.changed} 个标签。"
    if args.command == "video":
        report = extract_frames(args.input, args.start, args.interval, args.output)
        return f"已通过 {report.backend} 提取 {report.extracted_count} 张图片到 {report.output_folder}。"
    raise UtilityError(f"未知命令：{args.command}")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        print(run(args))
        return 0
    except UtilityError as error:
        print(f"错误：{error}", file=sys.stderr)
        return 2
    except OSError as error:
        print(f"系统错误：{error}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
