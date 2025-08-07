#!/usr/bin/env python3
"""
Debug script to analyze rack structure with detailed output
"""

import gzip
import xml.etree.ElementTree as ET
import json

def debug_analyze_rack(file_path):
    """Debug analysis of rack structure"""
    print(f"🔍 Analyzing: {file_path}")
    print("="*60)
    
    # Decompress and parse
    try:
        with gzip.open(file_path, 'rb') as f_in:
            xml_content = f_in.read()
            root = ET.fromstring(xml_content)
    except Exception as e:
        print(f"❌ Error: {e}")
        return
    
    # Save XML for inspection
    ET.indent(root, space="  ", level=0)
    tree = ET.ElementTree(root)
    tree.write("debug_output.xml", encoding='utf-8', xml_declaration=True)
    print("📄 XML saved to debug_output.xml")
    
    # Look for the main rack structure
    print("\n🔍 Looking for rack structure...")
    
    # Find all AudioEffectGroupDevice elements
    audio_groups = root.findall(".//AudioEffectGroupDevice")
    print(f"\n📦 Found {len(audio_groups)} AudioEffectGroupDevice elements")
    
    for i, group in enumerate(audio_groups):
        user_name_elem = group.find("UserName")
        name = user_name_elem.get("Value") if user_name_elem is not None else f"Group {i+1}"
        print(f"\n  📦 Audio Effect Group: {name}")
        
        # Check for branches
        branches = group.find("Branches")
        if branches is not None:
            print(f"    ✓ Has Branches element")
            
            # Look for AudioEffectBranchPreset in branches
            audio_branches = branches.findall(".//AudioEffectBranchPreset")
            print(f"    📁 Found {len(audio_branches)} AudioEffectBranchPreset elements")
            
            for j, branch in enumerate(audio_branches):
                branch_name_elem = branch.find("UserName")
                branch_name = branch_name_elem.get("Value") if branch_name_elem is not None else f"Branch {j+1}"
                print(f"      🔹 Branch: {branch_name}")
                
                # Look for devices in branch
                devices = branch.findall(".//DevicePresets")
                if devices:
                    for device_group in devices:
                        # Look for specific device types
                        eq3s = device_group.findall(".//Eq3")
                        print(f"        - Found {len(eq3s)} EQ3 devices")
                        
                        beat_repeats = device_group.findall(".//BeatRepeat")
                        print(f"        - Found {len(beat_repeats)} BeatRepeat devices")
                        
                        tubes = device_group.findall(".//Tube")
                        print(f"        - Found {len(tubes)} Tube (Dynamic Tube) devices")
                        
                        phasers = device_group.findall(".//Phaser")
                        print(f"        - Found {len(phasers)} Phaser devices")
                        
                        reverbs = device_group.findall(".//Reverb")
                        print(f"        - Found {len(reverbs)} Reverb devices")
                        
                        flangers = device_group.findall(".//Flanger")
                        print(f"        - Found {len(flangers)} Flanger devices")
    
    # Look for top-level devices after the nested rack
    print("\n🔍 Looking for top-level devices...")
    top_level_devices = root.find(".//DeviceChain/DeviceChain/Devices")
    if top_level_devices is not None:
        print("✓ Found top-level device chain")
        
        # Count each device type
        compressors = top_level_devices.findall(".//Compressor2")
        print(f"  - Found {len(compressors)} Compressor2 devices")
        
        tubes = top_level_devices.findall(".//Tube")
        print(f"  - Found {len(tubes)} Tube (Dynamic Tube) devices")

if __name__ == "__main__":
    # You'll need to provide the path to Weird_Dentist.adg
    import sys
    if len(sys.argv) > 1:
        debug_analyze_rack(sys.argv[1])
    else:
        print("Usage: python debug_analyzer.py <path_to_rack.adg>")
