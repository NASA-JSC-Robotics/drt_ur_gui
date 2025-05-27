#!/usr/bin/python3

import argparse
import xml.etree.ElementTree as ET

def main(filename: str):
    tree = ET.parse(filename)
    root = tree.getroot()
    fix_tree(root)
    tree.write(filename, encoding="utf-8", xml_declaration=True)
    return

def fix_tree(etree):
    for child in etree:
        if len(child) > 0:
            fix_tree(child)
        else:
            if child.text is not None and child.text.count('::') > 1:
                print(f"Problem attribute found: {child.text}")
                attribute_parts = child.text.split('::')
                child.text = '::'.join([attribute_parts[0], attribute_parts[-1]]) 
                print(f"Problem attribute altered to {child.text}")
    return

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog=
                '''
                ui file fixer
                This script is used to fix ui files that are altered by Qt Creator
                When you save a file in Qt Creator many of the property tag objects are updated with a class hierarchy that PySide2 understands, but not python_qt_bindings (the ros-indexed PySide2 package)
                For example, "Qt::Orientation::Vertical" will become "Qt:Vertical" after this script is ran on a UI file
                ''',
        description='Prepares Qt Creator generated .ui files for use with ROS2/python_qt_bindings',
        epilog='Bottom Text'
    )
    parser.add_argument('filename', help='Path to the ui file you would like to fix')
    args = parser.parse_args()
    main(args.filename)
