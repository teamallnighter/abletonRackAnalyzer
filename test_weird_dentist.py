#!/usr/bin/env python3
"""Test script to examine Weird_Dentist structure"""

import gzip
import xml.etree.ElementTree as ET
import sys

def examine_rack(file_path):
    """Examine the structure of the rack"""
    # Decompress
    with gzip.open(file_path, 'rb') as f:
        xml_content = f.read()
        root = ET.fromstring(xml_content)
    
    # Save XML for manual inspection
    ET.indent(root, space="  ", level=0)
    tree = ET.ElementTree(root)
    tree.write("weird_dentist_structure.xml", encoding='utf-8', xml_declaration=True)
    print("📄 XML saved to weird_dentist_structure.xml")
    
    print("\n🔍 Examining structure...")
    
    # Look for all AudioEffectGroupDevice elements
    print("\n📦 AudioEffectGroupDevice elements:")
    for i, device in enumerate(root.findall(".//AudioEffectGroupDevice")):
        name_elem = device.find("UserName")
        name = name_elem.get("Value") if name_elem is not None else f"Device {i}"
        print(f"  - {name}")
        
        # Check for branches
        branches = device.find("Branches")
        if branches is not None:
            print(f"    Has Branches: {len(branches)} children")
            # Look for branch types
            audio_branches = branches.findall("AudioEffectBranchPreset")
            print(f"    AudioEffectBranchPreset count: {len(audio_branches)}")
            
            for j, branch in enumerate(audio_branches):
                branch_name = branch.find("UserName")
                if branch_name is not None:
                    print(f"      Branch {j}: {branch_name.get('Value')}")
    
    # Look for the main device chain
    print("\n🔗 Main DeviceChain structure:")
    main_chain = root.find(".//Ableton/AudioEffectGroupDevice/DeviceChain")
    if main_chain is None:
        main_chain = root.find(".//Ableton/GroupDevicePreset/DeviceChain")
    
    if main_chain:
        devices = main_chain.find("Devices")
        if devices:
            print(f"  Found Devices container with {len(devices)} children")
            for child in devices:
                print(f"    - {child.tag}")
                if child.tag == "AudioEffectGroupDevice":
                    name = child.find("UserName")
                    if name is not None:
                        print(f"      Name: {name.get('Value')}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        examine_rack(sys.argv[1])
    else:
        print("Please provide the path to Weird_Dentist.adg")
