"""Compatibility wrapper for creating missing empty labels."""

from yolo_utils.labels import generate_empty_labels


def create_blank_annotation_files(folder1, folder2):
    return generate_empty_labels(folder1, folder2)


def main(folder1, folder2):
    report = create_blank_annotation_files(folder1, folder2)
    print(f"已补齐 {report.changed} 个空标签。")
    return report
