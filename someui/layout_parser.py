import xml.etree.ElementTree as ET
from someui import *


WIDGET_REGISTRY = {"Box": Container, "Label": Label, "Button": Button}


class XMLTemplateParser:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.ids = {}  # Сюда сложим все элементы по их id

    def parse(self, root_widget) -> Widget:
        tree = ET.parse(self.file_path)
        root_elem = tree.getroot()
        return self._build_tree(root_elem, root_widget)

    def _build_tree(self, xml_node: ET.Element, parent) -> Widget:
        tag_name = xml_node.tag
        attributes = xml_node.attrib

        widget_class = WIDGET_REGISTRY.get(tag_name, Widget)
        wdg = widget_class(parent, **attributes)

        if wdg.id:
            if wdg.id in self.ids:
                raise ValueError(f"Дублирующийся ID в разметке: '{wdg.id}'")
            self.ids[wdg.id] = wdg

        for child_xml in xml_node:
            child_widget = self._build_tree(child_xml, wdg)
            child_widget.parent = wdg
            wdg.children.append(child_widget)

        return wdg