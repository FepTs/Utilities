"""Compatibility wrapper for collision-safe batch renaming."""

from yolo_utils.files import rename_files


def main(input_dir, ext_filter="all", start_number=1):
    changes = rename_files(input_dir, ext_filter, start_number)
    print(f"已重命名 {len(changes)} 个文件。")
    return changes
