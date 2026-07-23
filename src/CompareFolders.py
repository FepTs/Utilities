"""Compatibility wrapper for non-destructive folder comparison."""

from yolo_utils.files import FolderComparison, compare_folders


def get_file_names(folder_path):
    report = compare_folders(folder_path, folder_path)
    return set(report.common)


def main(folder1, folder2):
    report = compare_folders(folder1, folder2)
    print(f"共有 {len(report.common)} 个同名文件。")
    print(f"文件夹 1 独有 {len(report.only_first)} 个文件。")
    print(f"文件夹 2 独有 {len(report.only_second)} 个文件。")
    return report


__all__ = ["FolderComparison", "compare_folders", "main"]
