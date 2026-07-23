"""Compatibility wrapper for YOLO label cleaning."""

from yolo_utils.labels import clean_labels


def main(folder_path, valid_classes):
    report = clean_labels(folder_path, valid_classes)
    print(f"已检查 {report.processed} 个标签，改写 {report.changed} 个。")
    return report
