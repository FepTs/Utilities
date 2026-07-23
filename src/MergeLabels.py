"""Compatibility wrapper for merging same-name YOLO labels."""

from yolo_utils.labels import merge_labels


def merge_annotation_files(folder1, folder2):
    return merge_labels(folder1, folder2)


def main(folder1, folder2):
    report = merge_annotation_files(folder1, folder2)
    print(f"已合并 {report.changed} 个标签。")
    return report
