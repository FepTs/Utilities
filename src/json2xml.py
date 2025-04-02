"""
v0.1
用于json文件转xml
"""
import os
from json import loads
from dicttoxml import dicttoxml
from xml.dom.minidom import parseString


def jsonToXml(json_path, xml_path):

    with open(json_path, 'r', encoding='UTF-8') as json_file:
        load_dict = loads(json_file.read())
    # print(load_dict)
    my_item_func = lambda x: 'Annotation'
    xml = dicttoxml(load_dict, custom_root='Annotations', item_func=my_item_func, attr_type=False)
    dom = parseString(xml)
    # print(dom.toprettyxml())
    # print(type(dom.toprettyxml()))
    with open(xml_path, 'w', encoding='UTF-8') as xml_file:
        xml_file.write(dom.toprettyxml())


def json_to_xml(json_dir, xml_dir):

    if (os.path.exists(xml_dir) == False):
        os.makedirs(xml_dir)
    dir = os.listdir(json_dir)
    for file in dir:
        file_list = file.split(".")
        if (file_list[-1] == 'json'):
            jsonToXml(os.path.join(json_dir, file), os.path.join(xml_dir, file_list[0] + '.xml'))


if __name__ == '__main__':

    j_dir = "F:/work/jsontoxml/json/"
    x_dir = "F:/work/jsontoxml/xml/"
    json_to_xml(j_dir, x_dir)
