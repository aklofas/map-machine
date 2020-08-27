"""
Extract icons from SVG file.

Author: Sergey Vartanov (me@enzet.ru).
"""
import re
import xml.dom.minidom

from typing import Dict

from roentgen import ui


class IconExtractor:
    """
    Extract icons from SVG file.

    Icon is a single path with "id" attribute that aligned to 16×16 grid.
    """
    def __init__(self, svg_file_name: str):
        """
        :param svg_file_name: input SVG file name with icons.  File may contain
            any other irrelevant graphics.
        """
        self.icons: Dict[str, (str, float, float)] = {}

        with open(svg_file_name) as input_file:
            content = xml.dom.minidom.parse(input_file)
            for element in content.childNodes:
                if element.nodeName == "svg":
                    for node in element.childNodes:
                        if node.nodeName in ["g", "path"]:
                            self.parse(node)

    def parse(self, node) -> None:
        """
        Extract icon paths into a map.

        :param node: XML node that contains icon
        """
        if node.nodeName == "path":
            if "id" in node.attributes.keys() and \
                    "d" in node.attributes.keys() and \
                    node.attributes["id"].value:
                path = node.attributes["d"].value
                m = re.match("[Mm] ([0-9.e-]*)[, ]([0-9.e-]*)", path)
                if not m:
                    ui.error(f"invalid path: {path}")
                else:
                    x = int(float(m.group(1)) / 16)
                    y = int(float(m.group(2)) / 16)
                    self.icons[node.attributes["id"].value] = \
                        (node.attributes["d"].value, x, y)
        else:
            for sub_node in node.childNodes:
                self.parse(sub_node)

    def get_path(self, id_: str) -> (str, float, float, bool):
        """
        Get SVG path of the icon.

        :param id_: string icon ID
        """
        if id_ in self.icons:
            return list(self.icons[id_]) + [True]
        else:
            if id_ == "no":
                return "M 4,4 L 4,10 10,10 10,4 z", 0, 0, False
            if id_ == "small":
                return "M 6,6 L 6,8 8,8 8,6 z", 0, 0, False
            ui.error(f"no such icon ID {id_}")
            return "M 4,4 L 4,10 10,10 10,4 z", 0, 0, False
