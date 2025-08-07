#!/usr/bin/env python3
"""
Ableton Rack Analyzer V2 - Fixed nested rack parsing
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

def get_device_type_name(device_type):
    """Convert device type to friendly name"""
    device_names = {
        'Eq3': 'EQ Three',
        'Tube': 'Dynamic Tube',
        'Compressor2': 'Compressor',
        'BeatRepeat': 'Beat Repeat',
        'Phaser': 'Phaser',
        'Reverb': 'Reverb',
        'Flanger': 'Flanger',
        'AudioEffectGroupDevice': 'Audio Effect Rack',
        'Gate': 'Gate',
        'Frequency': 'Frequency Shifter'
    }
    return device_names.get(device_type, device_type)

def parse_device(device_elem, device_type):
    """Parse a single device element"""
    # Get user name (preset name)
    user_name_elem = device_elem.find("UserName")
    preset_name = user_name_elem.get("Value") if user_name_elem is not None else ""
    
    # Get on/off status
    on_elem = device_elem.find("On/Manual")
    is_on = on_elem.get("Value") == "true" if on_elem is not None else True
    
    device_info = {
        "type": device_type,
        "name": get_device_type_name(device_type),
        "preset_name": preset_name if preset_name else None,
        "is_on": is_on
    }
    
    # If it's a rack, parse its chains
    if device_type == "AudioEffectGroupDevice":
        device_info["chains"] = parse_audio_effect_rack_chains(device_elem)
    
    return device_info

def parse_audio_effect_rack_chains(rack_elem):
    """Parse chains within an Audio Effect Rack"""
    chains = []
    
    # Find the Branches element
    branches = rack_elem.find("Branches")
    if branches is not None:
        # Look for AudioEffectBranchPreset elements
        for branch in branches.findall("AudioEffectBranchPreset"):
            # Get chain name
            user_name_elem = branch.find("UserName")
            chain_name = user_name_elem.get("Value") if user_name_elem is not None else "Unnamed Chain"
            
            # Check if soloed
            solo_elem = branch.find("IsSoloed")
            is_soloed = solo_elem.get("Value") == "true" if solo_elem is not None else False
            
            # Parse devices in this chain
            devices = []
            device_chain = branch.find("DeviceChain")
            if device_chain is not None:
                devices_elem = device_chain.find("Devices")
                if devices_elem is not None:
                    devices = parse_devices_in_container(devices_elem)
            
            chains.append({
                "name": chain_name,
                "is_soloed": is_soloed,
                "devices": devices
            })
    
    return chains

def parse_devices_in_container(devices_container):
    """Parse all devices within a Devices container"""
    devices = []
    
    # List of all device types to look for
    device_types = [
        'Eq3', 'Tube', 'Compressor2', 'BeatRepeat', 'Phaser', 
        'Reverb', 'Flanger', 'AudioEffectGroupDevice', 'Gate', 
        'Frequency', 'Eq8', 'Operator', 'AutoFilter', 'Delay',
        'Chorus', 'AutoPan', 'Limiter', 'MultibandDynamics',
        'Saturator', 'Vocoder', 'GlueCompressor', 'StereoGain'
    ]
    
    # Look for each device type
    for device_type in device_types:
        for device_elem in devices_container.findall(device_type):
            device_info = parse_device(device_elem, device_type)
            devices.append(device_info)
    
    return devices

def parse_chains_and_devices(xml_root, filename=None):
    """Parse the main rack structure"""
    rack_info = {
        "rack_name": os.path.splitext(os.path.basename(filename))[0] if filename else "Unknown",
        "use_case": os.path.splitext(os.path.basename(filename))[0] if filename else "Unknown",
        "macro_controls": [],
        "chains": []
    }
    
    # Get macro controls
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
    
    # Find the main device chain
    main_chain = xml_root.find(".//Ableton/GroupDevicePreset/DeviceChain")
    if main_chain is None:
        main_chain = xml_root.find(".//DeviceChain")
    
    if main_chain is not None:
        # Get the main chain name
        main_chain_name = "Main Chain"
        
        # Find devices in the main chain
        devices_elem = main_chain.find("Devices")
        if devices_elem is not None:
            devices = parse_devices_in_container(devices_elem)
            
            # Create a single main chain with all devices
            rack_info["chains"].append({
                "name": main_chain_name,
                "is_soloed": False,
                "devices": devices
            })
    
    return rack_info

def export_analysis_to_json(rack_info, original_file_path, output_folder="."):
    """Export the rack analysis to a JSON file"""
    try:
        base_name = os.path.splitext(os.path.basename(original_file_path))[0]
        output_file = os.path.join(output_folder, f"{base_name}_analysis_v2.json")
        
        with open(output_file, 'w') as f:
            json.dump(rack_info, f, indent=2)
        
        print(f"📊 Analysis exported to: {output_file}")
        return output_file
    except Exception as e:
        print(f"❌ Error exporting analysis: {e}")
        return None

def analyze_ableton_rack(file_path, export_json=True):
    """Main analysis function"""
    print(f"🔍 Analyzing: {file_path}")
    
    # Decompress and parse
    xml_root = decompress_and_parse_ableton_file(file_path)
    if xml_root is None:
        return None
    
    # Analyze structure
    rack_info = parse_chains_and_devices(xml_root, file_path)
    
    # Export if requested
    if export_json:
        export_analysis_to_json(rack_info, file_path)
    
    # Print summary
    print(f"\n📋 SUMMARY:")
    print(f"  Rack: {rack_info['rack_name']}")
    print(f"  Macros: {len(rack_info['macro_controls'])}")
    print(f"  Chains: {len(rack_info['chains'])}")
    
    # Count total devices including nested
    total_devices = 0
    for chain in rack_info['chains']:
        total_devices += count_devices_recursive(chain['devices'])
    print(f"  Total Devices: {total_devices}")
    
    return rack_info

def count_devices_recursive(devices):
    """Count devices including those in nested racks"""
    count = len(devices)
    for device in devices:
        if 'chains' in device:
            for chain in device['chains']:
                count += count_devices_recursive(chain['devices'])
    return count

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        analyze_ableton_rack(sys.argv[1])
    else:
        print("Usage: python abletonRackAnalyzer_v2.py <rack_file.adg>")
