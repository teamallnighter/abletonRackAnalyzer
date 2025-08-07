#!/usr/bin/env python3
import gzip
import xml.etree.ElementTree as ET
import sys

if len(sys.argv) > 1:
    with gzip.open(sys.argv[1], 'rb') as f:
        xml_content = f.read()
        root = ET.fromstring(xml_content)
        
    ET.indent(root, space="  ", level=0)
    tree = ET.ElementTree(root)
    tree.write("weird_dentist.xml", encoding='utf-8', xml_declaration=True)
    print("XML extracted to weird_dentist.xml")
else:
    print("Usage: python extract_xml.py <path_to_adg_file>")
