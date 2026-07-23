"""Compatibility wrapper for standard-library JSON to XML conversion."""

from yolo_utils.converters import convert_json_folder_to_xml, convert_json_to_xml


def jsonToXml(json_path, xml_path):
    return convert_json_to_xml(json_path, xml_path)


def json_to_xml(json_dir, xml_dir):
    return convert_json_folder_to_xml(json_dir, xml_dir)
