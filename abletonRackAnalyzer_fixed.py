#!/usr/bin/env python3
"""
Ableton Rack Analyzer - Fixed version for proper nested rack handling
"""

import gzip
import xml.etree.ElementTree as ET
import os
import json

def decompress_and_parse_ableton_file(file_path):
    """Decompresses an Ableton .adg or .adv file and parses its XML content."""
    try:
        with gzip.open(file_path, 'rb') as f_in:
            xml_content = f_in.read()
            root = ET.fromstring(xml_content)
            return root
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def parse_device(device_elem, device_type):
    """Parse a single device"""
    user_name_elem = device_elem.find("UserName")
    user_name = user_name_elem.get("Value") if user_name_elem is not None else ""
    
    on_elem = device_elem.find("On/Manual")
    is_on = on_elem.get("Value") == "true" if on_elem is not None else True
    
    device_info = {
        "type": device_type,
        "name": user_name if user_name else device_type,
        "is_on": is_on
    }
    
    # If it's an AudioEffectGroupDevice (nested rack), parse its chains
    if device_type == "AudioEffectGroupDevice":
        branches = device_elem.find("Branches")
        if branches is not None:
            device_info["chains"] = []
            # Parse each branch as a chain
            for branch in branches.findall("AudioEffectBranchPreset"):
                chain_name_elem = branch.find("UserName")
                chain_name = chain_name_elem.get("Value") if chain_name_elem is not None else "Unnamed Chain"
                
                solo_elem = branch.find("IsSoloed")
                is_soloed = solo_elem.get("Value") == "true" if solo_elem is not None else False
                
                # Parse devices in this chain
                chain_devices = []
                device_chain = branch.find("DeviceChain")
                if device_chain is not None:
                    devices_container = device_chain.find("Devices")
                    if devices_container is not None:
                        chain_devices = parse_devices_from_container(devices_container)
                
                device_info["chains"].append({
                    "name": chain_name,
                    "is_soloed": is_soloed,
                    "devices": chain_devices
                })
    
    return device_info

def parse_devices_from_container(devices_container):
    """Parse all devices from a Devices container"""
    devices = []
    
    # Map of device types we care about
    device_types = {
        'AudioEffectGroupDevice': 'Audio Effect Rack',
        'Eq3': 'EQ Three',
        'Tube': 'Dynamic Tube',
        'Compressor2': 'Compressor',
        'BeatRepeat': 'Beat Repeat',
        'Phaser': 'Phaser',
        'Reverb': 'Reverb',
        'Flanger': 'Flanger',
        'Eq8': 'EQ Eight',
        'Gate': 'Gate',
        'Delay': 'Delay',
        'AutoFilter': 'Auto Filter',
        'Saturator': 'Saturator',
        'GlueCompressor': 'Glue Compressor',
        'Limiter': 'Limiter',
        'Chorus': 'Chorus',
        'FrequencyShifter': 'Frequency Shifter',
        'Resonator': 'Resonator',
        'AutoPan': 'Auto Pan',
        'Redux': 'Redux',
        'FilterDelay': 'Filter Delay'
    }
    
    # Check each child element
    for child in devices_container:
        if child.tag in device_types:
            device_info = parse_device(child, child.tag)
            devices.append(device_info)
    
    return devices

def parse_chains_and_devices(xml_root, filename=None, verbose=False):
    """Parse the main rack structure"""
    rack_info = {
        "rack_name": os.path.splitext(os.path.basename(filename))[0] if filename else "Unknown",
        "use_case": os.path.splitext(os.path.basename(filename))[0] if filename else "Unknown",
        "macro_controls": [],
        "chains": []
    }
    
    # Parse macro controls
    for i in range(16):
        macro_name_elem = xml_root.find(f".//MacroDisplayNames.{i}")
        if macro_name_elem is not None:
            macro_name = macro_name_elem.get("Value", f"Macro {i+1}")
            if macro_name != f"Macro {i+1}":
                macro_control_elem = xml_root.find(f".//MacroControls.{i}/Manual")
                macro_value = float(macro_control_elem.get("Value", "0")) if macro_control_elem is not None else 0.0
                rack_info["macro_controls"].append({
                    "name": macro_name,
                    "value": macro_value,
                    "index": i
                })
    
    # Find the main AudioEffectGroupDevice (the root rack)
    main_rack = xml_root.find(".//Ableton/AudioEffectGroupDevice")
    if main_rack is None:
        main_rack = xml_root.find(".//AudioEffectGroupDevice")
    
    if main_rack is not None:
        # Get the main device chain
        device_chain = main_rack.find("DeviceChain")
        if device_chain is not None:
            devices_container = device_chain.find("Devices")
            if devices_container is not None:
                # Parse all devices in the main chain
                devices = parse_devices_from_container(devices_container)
                
                # Create a single main chain containing all devices
                rack_info["chains"].append({
                    "name": "Main Chain",
                    "is_soloed": False,
                    "devices": devices
                })
    
    return rack_info

def export_xml_to_file(xml_root, original_file_path, output_folder="."):
    """Export XML content to file"""
    try:
        base_name = os.path.splitext(os.path.basename(original_file_path))[0]
        output_file = os.path.join(output_folder, f"{base_name}.xml")
        
        ET.indent(xml_root, space="  ", level=0)
        tree = ET.ElementTree(xml_root)
        tree.write(output_file, encoding='utf-8', xml_declaration=True)
        
        print(f"📄 XML exported to: {output_file}")
        return output_file
    except Exception as e:
        print(f"❌ Error exporting XML: {e}")
        return None

def export_analysis_to_json(rack_info, original_file_path, output_folder="."):
    """Export analysis to JSON"""
    try:
        base_name = os.path.splitext(os.path.basename(original_file_path))[0]
        output_file = os.path.join(output_folder, f"{base_name}_analysis.json")
        
        with open(output_file, 'w') as f:
            json.dump(rack_info, f, indent=2)
        
        print(f"📊 Analysis exported to: {output_file}")
        return output_file
    except Exception as e:
        print(f"❌ Error exporting analysis: {e}")
        return None

def print_rack_structure(rack_info):
    """Print the rack structure in a readable format"""
    print(f"\n🎛️ Rack: {rack_info['rack_name']}")
    print(f"📎 Macros: {len(rack_info['macro_controls'])}")
    
    for chain in rack_info['chains']:
        print(f"\n📁 {chain['name']}")
        for device in chain['devices']:
            status = "🟢" if device.get('is_on', True) else "🔴"
            print(f"  {status} {device['name']} ({device['type']})")
            
            # If device has nested chains (it's a rack), show them
            if 'chains' in device:
                for nested_chain in device['chains']:
                    solo = " (SOLO)" if nested_chain.get('is_soloed') else ""
                    print(f"    📁 {nested_chain['name']}{solo}")
                    for nested_device in nested_chain['devices']:
                        status = "🟢" if nested_device.get('is_on', True) else "🔴"
                        print(f"      {status} {nested_device['name']} ({nested_device['type']})")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        root = decompress_and_parse_ableton_file(sys.argv[1])
        if root:
            rack_info = parse_chains_and_devices(root, sys.argv[1])
            print_rack_structure(rack_info)
            export_analysis_to_json(rack_info, sys.argv[1])
