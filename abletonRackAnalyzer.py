import gzip
import xml.etree.ElementTree as ET
import os
import json

def decompress_and_parse_ableton_file(file_path):
    """
    Decompresses an Ableton .adg or .adv file and parses its XML content.

    Args:
        file_path (str): The path to the .adg or .adv file.

    Returns:
        xml.etree.ElementTree.Element: The root element of the parsed XML,
                                      or None if an error occurs.
    """
    try:
        with gzip.open(file_path, 'rb') as f_in:
            xml_content = f_in.read()
            root = ET.fromstring(xml_content)
            return root
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
        return None
    except Exception as e:
        print(f"Error decompressing or parsing file: {e}")
        return None

def export_xml_to_file(xml_root, original_file_path, output_folder="."):
    """
    Exports the XML content to a file in the specified folder.
    
    Args:
        xml_root: The XML root element
        original_file_path (str): The original .adg/.adv file path
        output_folder (str): The folder to save the XML file (default: current folder)
    
    Returns:
        str: The path of the exported XML file, or None if failed
    """
    try:
        # Get the filename without extension and path
        base_name = os.path.splitext(os.path.basename(original_file_path))[0]
        output_file = os.path.join(output_folder, f"{base_name}.xml")
        
        # Format the XML with proper indentation
        ET.indent(xml_root, space="  ", level=0)
        
        # Create ElementTree and write to file
        tree = ET.ElementTree(xml_root)
        tree.write(output_file, encoding='utf-8', xml_declaration=True)
        
        print(f"XML exported to: {output_file}")
        return output_file
        
    except Exception as e:
        print(f"Error exporting XML: {e}")
        return None

def parse_chains_and_devices(xml_root):
    """Parse the chain structure and devices in each chain"""
    if xml_root is None:
        return None
    
    rack_info = {
        "rack_name": "Unknown",
        "ableton_version": f"{xml_root.get('MajorVersion', '')}.{xml_root.get('MinorVersion', '')}",
        "creator": xml_root.get("Creator", ""),
        "macro_controls": [],
        "chains": []
    }
    
    # Get macro controls from the top level
    print("=== MACRO CONTROLS ===")
    for i in range(16):
        macro_name_elem = xml_root.find(f".//MacroDisplayNames.{i}")
        if macro_name_elem is not None:
            macro_name = macro_name_elem.get("Value", f"Macro {i+1}")
            macro_control_elem = xml_root.find(f".//MacroControls.{i}/Manual")
            macro_value = "0"
            if macro_control_elem is not None:
                macro_value = macro_control_elem.get("Value", "0")
            
            if macro_name != f"Macro {i+1}":  # Only show named macros
                print(f"  {macro_name}: {macro_value}")
                rack_info["macro_controls"].append({
                    "name": macro_name,
                    "value": float(macro_value),
                    "index": i
                })
    
    # Find all InstrumentBranchPreset elements (these are the chains)
    print("\n=== CHAINS AND DEVICES ===")
    branch_presets = xml_root.findall(".//InstrumentBranchPreset")
    
    for i, branch in enumerate(branch_presets):
        # Get chain name
        name_elem = branch.find("Name")
        chain_name = name_elem.get("Value") if name_elem is not None else f"Chain {i+1}"
        
        # Check if chain is soloed
        solo_elem = branch.find("IsSoloed")
        is_soloed = solo_elem.get("Value") == "true" if solo_elem is not None else False
        
        print(f"\n--- Chain: {chain_name} {'(SOLOED)' if is_soloed else ''} ---")
        
        chain_info = {
            "name": chain_name,
            "is_soloed": is_soloed,
            "devices": []
        }
        
        # Find devices in this chain
        device_presets = branch.findall(".//DevicePresets")
        for device_preset_group in device_presets:
            devices_found = []
            
            # Look for different types of devices
            # 1. Operator devices
            operators = device_preset_group.findall(".//Operator")
            for op in operators:
                user_name_elem = op.find("UserName")
                user_name = user_name_elem.get("Value") if user_name_elem is not None else ""
                device_name = user_name if user_name else "Operator"
                
                # Check if device is on
                on_elem = op.find("On/Manual")
                is_on = on_elem.get("Value") == "true" if on_elem is not None else True
                
                device_info = {
                    "type": "Operator",
                    "name": device_name,
                    "is_on": is_on
                }
                devices_found.append(device_info)
                print(f"  Device: {device_name} (Operator) - {'ON' if is_on else 'OFF'}")
            
            # 2. EQ8 devices
            eq8_devices = device_preset_group.findall(".//Eq8")
            for eq in eq8_devices:
                user_name_elem = eq.find("UserName")
                user_name = user_name_elem.get("Value") if user_name_elem is not None else ""
                device_name = user_name if user_name else "EQ Eight"
                
                # Check if device is on
                on_elem = eq.find("On/Manual")
                is_on = on_elem.get("Value") == "true" if on_elem is not None else True
                
                device_info = {
                    "type": "Eq8",
                    "name": device_name,
                    "is_on": is_on
                }
                devices_found.append(device_info)
                print(f"  Device: {device_name} (EQ Eight) - {'ON' if is_on else 'OFF'}")
            
            # 3. Look for other Ableton devices by tag name
            common_devices = ['Compressor2', 'AutoFilter', 'Reverb', 'Delay', 'Chorus', 
                            'Phaser', 'AutoPan', 'Gate', 'Limiter', 'MultibandDynamics',
                            'Saturator', 'Frequency', 'Vocoder', 'Bass', 'DrumRack', 
                            'Collision', 'Tension', 'Impulse', 'Simpler', 'Wavetable',
                            'GlueCompressor', 'Shifter', 'PhaserNew', 'StereoGain',
                            'AudioBranchMixerDevice', 'MxDeviceAudioEffect']
            
            for device_type in common_devices:
                devices = device_preset_group.findall(f".//{device_type}")
                for device in devices:
                    user_name_elem = device.find("UserName")
                    user_name = user_name_elem.get("Value") if user_name_elem is not None else ""
                    device_name = user_name if user_name else device_type
                    
                    # Check if device is on
                    on_elem = device.find("On/Manual")
                    is_on = on_elem.get("Value") == "true" if on_elem is not None else True
                    
                    device_info = {
                        "type": device_type,
                        "name": device_name,
                        "is_on": is_on
                    }
                    devices_found.append(device_info)
                    print(f"  Device: {device_name} ({device_type}) - {'ON' if is_on else 'OFF'}")
            
            # 4. Look for generic AbletonDevicePreset elements
            generic_devices = device_preset_group.findall(".//AbletonDevicePreset")
            for device_preset in generic_devices:
                # Try to find the actual device inside
                device_elem = device_preset.find("Device")
                if device_elem is not None:
                    # Get the first child which should be the actual device
                    for child in device_elem:
                        device_type = child.tag
                        user_name_elem = child.find("UserName")
                        user_name = user_name_elem.get("Value") if user_name_elem is not None else ""
                        device_name = user_name if user_name else device_type
                        
                        # Check if device is on
                        on_elem = child.find("On/Manual")
                        is_on = on_elem.get("Value") == "true" if on_elem is not None else True
                        
                        device_info = {
                            "type": device_type,
                            "name": device_name,
                            "is_on": is_on
                        }
                        
                        # Only add if not already found
                        if not any(d["type"] == device_type and d["name"] == device_name for d in devices_found):
                            devices_found.append(device_info)
                            print(f"  Device: {device_name} ({device_type}) - {'ON' if is_on else 'OFF'}")
            
            chain_info["devices"].extend(devices_found)
        
        if not chain_info["devices"]:
            print("  No devices found in this chain")
        
        rack_info["chains"].append(chain_info)
    
    return rack_info

def export_analysis_to_json(rack_info, original_file_path, output_folder="."):
    """
    Export the rack analysis to a JSON file.
    
    Args:
        rack_info: The analyzed rack information
        original_file_path (str): The original .adg/.adv file path
        output_folder (str): The folder to save the JSON file
    
    Returns:
        str: The path of the exported JSON file, or None if failed
    """
    try:
        base_name = os.path.splitext(os.path.basename(original_file_path))[0]
        output_file = os.path.join(output_folder, f"{base_name}_analysis.json")
        
        with open(output_file, 'w') as f:
            json.dump(rack_info, f, indent=2)
        
        print(f"Analysis exported to: {output_file}")
        return output_file
        
    except Exception as e:
        print(f"Error exporting analysis: {e}")
        return None

def print_summary(rack_info):
    """Print a summary of the rack structure"""
    if not rack_info:
        return
    
    print(f"\n{'='*60}")
    print("RACK ANALYSIS SUMMARY")
    print(f"{'='*60}")
    
    print(f"Ableton Version: {rack_info['ableton_version']}")
    print(f"Creator: {rack_info['creator']}")
    
    print(f"\nNamed Macro Controls: {len(rack_info['macro_controls'])}")
    for macro in rack_info['macro_controls']:
        print(f"  • {macro['name']}: {macro['value']}")
    
    print(f"\nChains: {len(rack_info['chains'])}")
    total_devices = 0
    for chain in rack_info['chains']:
        total_devices += len(chain['devices'])
        print(f"\n📁 {chain['name']} {'(SOLOED)' if chain['is_soloed'] else ''}")
        print(f"   Devices: {len(chain['devices'])}")
        for device in chain['devices']:
            status = "🟢" if device['is_on'] else "🔴"
            print(f"   {status} {device['name']} ({device['type']})")
    
    print(f"\nTotal Devices Across All Chains: {total_devices}")

def analyze_ableton_rack(file_path, export_xml=True, export_json=True, output_folder="."):
    """
    Main function to decompress, parse, and analyze an Ableton rack file.
    
    Args:
        file_path (str): Path to the .adg or .adv file
        export_xml (bool): Whether to export the decompressed XML
        export_json (bool): Whether to export the analysis as JSON
        output_folder (str): Folder to save exported files
    
    Returns:
        dict: The rack analysis information, or None if failed
    """
    print(f"Analyzing Ableton rack: {os.path.basename(file_path)}")
    print("="*60)
    
    # Step 1: Decompress and parse XML
    xml_root = decompress_and_parse_ableton_file(file_path)
    
    if xml_root is None:
        print("Failed to decompress and parse the file.")
        return None
    
    print(f"Successfully decompressed and parsed: {file_path}")
    
    # Step 2: Export XML if requested
    if export_xml:
        export_xml_to_file(xml_root, file_path, output_folder)
    
    # Step 3: Analyze chains and devices
    rack_info = parse_chains_and_devices(xml_root)
    
    if rack_info is None:
        print("Failed to analyze rack structure.")
        return None
    
    # Step 4: Print summary
    print_summary(rack_info)
    
    # Step 5: Export JSON analysis if requested
    if export_json:
        export_analysis_to_json(rack_info, file_path, output_folder)
    
    return rack_info

# Execute
if __name__ == "__main__":
    # You can change this path to analyze different racks
    rack_file = "/Volumes/ABLETON/User Library/Mr. Bill - 99 Racks/!MR. BILL - BASS - BASIC REESE [GENERATOR].adg"
    
    # Analyze the rack (exports both XML and JSON by default)
    analysis = analyze_ableton_rack(
        file_path=rack_file,
        export_xml=True,
        export_json=True,
        output_folder="."
    )
    
    if analysis:
        print(f"\n✅ Analysis complete! Check the exported files.")
    else:
        print(f"\n❌ Analysis failed.")
