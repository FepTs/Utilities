"""Reliable and reproducible dataset splitting."""

from __future__ import annotations

import json
import random
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path

from .common import (
    IMAGE_SUFFIXES,
    UtilityError,
    ensure_distinct_paths,
    index_unique_stems,
    require_directory,
    visible_files,
)


@dataclass(frozen=True)
class DetectionSample:
    image: Path
    label: Path


@dataclass(frozen=True)
class SplitReport:
    task: str
    train_count: int
    validation_count: int
    skipped_images: tuple[str, ...] = ()
    orphan_labels: tuple[str, ...] = ()
    seed: int = 42

    @property
    def total_count(self) -> int:
        return self.train_count + self.validation_count


def _validate_ratio(train_ratio: float) -> float:
    try:
        ratio = float(train_ratio)
    except (TypeError, ValueError) as error:
        raise UtilityError("训练集比例必须是数字。") from error
    if not 0.0 < ratio < 1.0:
        raise UtilityError("训练集比例必须大于 0 且小于 1。")
    return ratio


def _split_count(size: int, ratio: float) -> int:
    if size < 2:
        raise UtilityError("至少需要 2 个有效样本才能同时生成训练集和验证集。")
    return min(size - 1, max(1, int(size * ratio)))


def _prepare_destination(source: Path, destination: Path) -> Path:
    destination = destination.expanduser().resolve()
    ensure_distinct_paths(source, destination)
    if destination.exists():
        if not destination.is_dir():
            raise UtilityError(f"输出路径不是文件夹：{destination}")
        if any(destination.iterdir()):
            raise UtilityError(f"输出目录必须为空：{destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    return destination


def _publish_staged_output(staging: Path, destination: Path) -> None:
    if destination.exists():
        destination.rmdir()  # only succeeds for the empty directory validated above
    staging.replace(destination)


def _write_manifest(staging: Path, report: SplitReport, subsets: dict[str, list[str]]) -> None:
    payload = {
        "version": 1,
        "task": report.task,
        "seed": report.seed,
        "train_count": report.train_count,
        "validation_count": report.validation_count,
        "skipped_images": list(report.skipped_images),
        "orphan_labels": list(report.orphan_labels),
        "subsets": subsets,
    }
    (staging / "split_manifest.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def collect_detection_samples(
    input_path: str | Path,
) -> tuple[list[DetectionSample], tuple[str, ...], tuple[str, ...]]:
    source = require_directory(input_path, "输入目录")
    images_dir = require_directory(source / "images", "图片目录")
    labels_dir = require_directory(source / "labels", "标签目录")

    images = index_unique_stems(visible_files(images_dir, IMAGE_SUFFIXES), "图片目录")
    labels = index_unique_stems(visible_files(labels_dir, {".txt"}), "标签目录")

    common = sorted(images.keys() & labels.keys())
    samples = [DetectionSample(images[key], labels[key]) for key in common]
    skipped = tuple(images[key].name for key in sorted(images.keys() - labels.keys()))
    orphaned = tuple(labels[key].name for key in sorted(labels.keys() - images.keys()))
    if not samples:
        raise UtilityError("没有找到图片与同名 .txt 标签组成的有效样本对。")
    return samples, skipped, orphaned


def split_detection_dataset(
    input_path: str | Path,
    output_path: str | Path,
    train_ratio: float,
    *,
    seed: int = 42,
) -> SplitReport:
    """Split image/label pairs together; images and labels are never shuffled separately."""
    source = require_directory(input_path, "输入目录")
    destination = _prepare_destination(source, Path(output_path))
    ratio = _validate_ratio(train_ratio)
    samples, skipped, orphaned = collect_detection_samples(source)

    shuffled = list(samples)
    random.Random(seed).shuffle(shuffled)
    train_size = _split_count(len(shuffled), ratio)
    grouped = {"train": shuffled[:train_size], "val": shuffled[train_size:]}
    report = SplitReport(
        task="detection",
        train_count=len(grouped["train"]),
        validation_count=len(grouped["val"]),
        skipped_images=skipped,
        orphan_labels=orphaned,
        seed=seed,
    )

    staging = Path(tempfile.mkdtemp(prefix=f".{destination.name}.", dir=destination.parent))
    try:
        manifest_subsets: dict[str, list[str]] = {}
        for subset, subset_samples in grouped.items():
            image_output = staging / subset / "images"
            label_output = staging / subset / "labels"
            image_output.mkdir(parents=True)
            label_output.mkdir(parents=True)
            manifest_subsets[subset] = []
            for sample in subset_samples:
                shutil.copy2(sample.image, image_output / sample.image.name)
                shutil.copy2(sample.label, label_output / sample.label.name)
                manifest_subsets[subset].append(sample.image.name)
        _write_manifest(staging, report, manifest_subsets)
        _publish_staged_output(staging, destination)
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return report


def split_classification_dataset(
    input_path: str | Path,
    output_path: str | Path,
    train_ratio: float,
    *,
    seed: int = 42,
) -> SplitReport:
    source = require_directory(input_path, "输入目录")
    destination = _prepare_destination(source, Path(output_path))
    ratio = _validate_ratio(train_ratio)
    class_dirs = sorted(
        (item for item in source.iterdir() if item.is_dir() and not item.name.startswith(".")),
        key=lambda item: item.name.casefold(),
    )
    if not class_dirs:
        raise UtilityError("输入目录中没有找到类别子目录。")

    rng = random.Random(seed)
    grouped: dict[str, dict[str, list[Path]]] = {}
    for class_dir in class_dirs:
        images = visible_files(class_dir, IMAGE_SUFFIXES)
        if len(images) < 2:
            raise UtilityError(f"类别“{class_dir.name}”至少需要 2 张图片。")
        rng.shuffle(images)
        train_size = _split_count(len(images), ratio)
        grouped[class_dir.name] = {
            "train": images[:train_size],
            "val": images[train_size:],
        }

    train_count = sum(len(group["train"]) for group in grouped.values())
    validation_count = sum(len(group["val"]) for group in grouped.values())
    report = SplitReport("classification", train_count, validation_count, seed=seed)
    staging = Path(tempfile.mkdtemp(prefix=f".{destination.name}.", dir=destination.parent))
    try:
        manifest_subsets: dict[str, list[str]] = {"train": [], "val": []}
        for class_name, group in grouped.items():
            for subset in ("train", "val"):
                target = staging / subset / class_name
                target.mkdir(parents=True)
                for image in group[subset]:
                    shutil.copy2(image, target / image.name)
                    manifest_subsets[subset].append(f"{class_name}/{image.name}")
        _write_manifest(staging, report, manifest_subsets)
        _publish_staged_output(staging, destination)
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return report


def split_dataset(
    input_path: str | Path,
    output_path: str | Path,
    train_ratio: float,
    task: str = "detection",
    *,
    seed: int = 42,
) -> SplitReport:
    normalized = str(task).strip().lower()
    if normalized in {"0", "detection", "detect"}:
        return split_detection_dataset(input_path, output_path, train_ratio, seed=seed)
    if normalized in {"1", "classification", "classify"}:
        return split_classification_dataset(input_path, output_path, train_ratio, seed=seed)
    raise UtilityError("任务类型必须是 detection（目标检测）或 classification（分类）。")


def format_split_report(report: SplitReport) -> str:
    lines = [
        f"划分完成：训练集 {report.train_count} 个，验证集 {report.validation_count} 个。",
        f"随机种子：{report.seed}（可使用同一种子复现结果）",
    ]
    if report.skipped_images:
        lines.append(f"跳过无标签图片 {len(report.skipped_images)} 个。")
    if report.orphan_labels:
        lines.append(f"发现无对应图片标签 {len(report.orphan_labels)} 个。")
    return "\n".join(lines)
