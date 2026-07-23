"""Compatibility wrapper for dataset splitting."""

from yolo_utils.dataset import (
    collect_detection_samples,
    format_split_report,
    split_classification_dataset,
    split_dataset,
    split_detection_dataset,
)

__all__ = [
    "collect_detection_samples",
    "split_detection_dataset",
    "split_classification_dataset",
    "split_dataset",
    "main",
]


def main(input_path, output_path, train_ratio, task="0", seed=42):
    report = split_dataset(input_path, output_path, train_ratio, task, seed=seed)
    print(format_split_report(report))
    return report


if __name__ == "__main__":
    from yolo_utils.cli import main as cli_main

    raise SystemExit(cli_main(["split", *(__import__("sys").argv[1:])]))
