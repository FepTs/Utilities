"""Compatibility wrapper for batch deletion."""

from yolo_utils.files import delete_paths, matching_files


def delete_files(input_folder, feature, extension, *, confirm=False):
    matches = matching_files(input_folder, feature, extension)
    if not confirm:
        print(f"匹配 {len(matches)} 个文件；为避免误删，调用时需传入 confirm=True。")
        return 0
    count = delete_paths(matches)
    print(f"已删除 {count} 个文件。")
    return count


def main(input_folder, feature, extension, *, confirm=False):
    return delete_files(input_folder, feature, extension, confirm=confirm)
