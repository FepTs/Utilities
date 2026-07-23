"""Compatibility wrapper for LabelMe JSON to YOLO conversion."""

from yolo_utils.converters import (
    convert_json_folder_to_yolo,
)


def main(input, output, map):
    report = convert_json_folder_to_yolo(input, output, map)
    print(f"已转换 {report.converted} 个 JSON。")
    return report
