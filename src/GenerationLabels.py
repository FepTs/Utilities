"""Compatibility wrapper for generating uniform labels.

Importing this module has no file-system side effects.
"""

from yolo_utils.labels import generate_uniform_labels


def main(input_folder, output_folder, label_content):
    report = generate_uniform_labels(input_folder, output_folder, label_content)
    print(f"已生成 {report.changed} 个标签。")
    return report
