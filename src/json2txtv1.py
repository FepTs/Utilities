"""Deprecated compatibility wrapper for LabelMe JSON to YOLO conversion."""

from warnings import warn

from yolo_utils.converters import convert_json_folder_to_yolo


def main(input, output, map):
    warn("json2txtv1 已合并到统一转换器，请改用 json2txtv2。", DeprecationWarning)
    return convert_json_folder_to_yolo(input, output, map)
