#!/usr/bin/env python3
"""
Ableton Rack Analyzer
A comprehensive tool for analyzing Ableton Live rack files (.adg/.adv)
Updated to match CLI functionality with enhanced nested rack support
"""

import gzip
import xml.etree.ElementTree as ET
import os
import json
from pathlib import Path

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
        print(f"❌ Error: File not found at {file_path}")
        return None
    except Exception as e:
        print(f"❌ Error decompressing or parsing file: {e}")
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
        
        print(f"📄 XML exported to: {output_file}")
        return output_file
        
    except Exception as e:
        print(f"❌ Error exporting XML: {e}")
        return None

def parse_chains_and_devices(xml_root, filename=None, verbose=False):
    """Parse the chain structure and devices in each chain"""
    if xml_root is None:
        return None
    
    # Extract use case from filename
    use_case = "Unknown"
    if filename:
        # Get the base name without extension and path
        base_name = os.path.splitext(os.path.basename(filename))[0]
        use_case = base_name
    
    rack_info = {
        "rack_name": "Unknown",
        "use_case": use_case,
        "macro_controls": [],
        "chains": []
    }
    
    # Get macro controls from the top level
    if verbose:
        print("\n📎 MACRO CONTROLS:")
    
    for i in range(16):
        macro_name_elem = xml_root.find(f".//MacroDisplayNames.{i}")
        if macro_name_elem is not None:
            macro_name = macro_name_elem.get("Value", f"Macro {i+1}")
            macro_control_elem = xml_root.find(f".//MacroControls.{i}/Manual")
            macro_value = "0"
            if macro_control_elem is not None:
                macro_value = macro_control_elem.get("Value", "0")
            
            if macro_name != f"Macro {i+1}":  # Only show named macros
                if verbose:
                    print(f"  • {macro_name}: {macro_value}")
                rack_info["macro_controls"].append({
                    "name": macro_name,
                    "value": float(macro_value),
                    "index": i
                })
    
    # Find chains and devices - handle both Instrument Racks and Audio Effect Racks
    if verbose:
        print(f"\n🔗 CHAINS AND DEVICES:")
    
    # Look for InstrumentBranchPreset elements (Instrument Racks)
    branch_presets = xml_root.findall(".//InstrumentBranchPreset")
    
    # Look for AudioEffectGroupDevice structure (Audio Effect Racks)
    audio_effect_groups = xml_root.findall(".//AudioEffectGroupDevice")
    
    # Process Instrument Rack chains
    for i, branch in enumerate(branch_presets):
        # Get chain name
        name_elem = branch.find("Name")
        chain_name = name_elem.get("Value") if name_elem is not None else f"Chain {i+1}"
        
        # Check if chain is soloed
        solo_elem = branch.find("IsSoloed")
        is_soloed = solo_elem.get("Value") == "true" if solo_elem is not None else False
        
        if verbose:
            print(f"\n🎹 Chain: {chain_name} {'(SOLOED)' if is_soloed else ''}")
        
        chain_info = {
            "name": chain_name,
            "is_soloed": is_soloed,
            "devices": []
        }
        
        # Find devices in this chain
        device_presets = branch.findall(".//DevicePresets")
        for device_preset_group in device_presets:
            devices_found = parse_devices_in_group(device_preset_group, verbose, 0)
            chain_info["devices"].extend(devices_found)
        
        if not chain_info["devices"] and verbose:
            print("  ❌ No devices found in this chain")
        
        rack_info["chains"].append(chain_info)
    
    # Look for AudioEffectBranchPreset elements (Audio Effect Racks)
    audio_effect_branches = xml_root.findall(".//AudioEffectBranchPreset")
    
    # Process Audio Effect Branch chains (Audio Effect Racks)
    for i, branch in enumerate(audio_effect_branches):
        # Get chain name from UserName
        user_name_elem = branch.find("UserName")
        chain_name = user_name_elem.get("Value") if user_name_elem is not None else f"Audio Chain {i+1}"
        
        # Check if chain is soloed
        solo_elem = branch.find("IsSoloed")
        is_soloed = solo_elem.get("Value") == "true" if solo_elem is not None else False
        
        if verbose:
            print(f"\n📁 Audio Effect Chain: {chain_name} {'(SOLOED)' if is_soloed else ''}")
        
        chain_info = {
            "name": chain_name,
            "is_soloed": is_soloed,
            "devices": []
        }
        
        # Find devices in this audio effect branch
        device_presets = branch.findall(".//DevicePresets")
        for device_preset_group in device_presets:
            devices_found = parse_devices_in_group(device_preset_group, verbose, 0)
            chain_info["devices"].extend(devices_found)
        
        if not chain_info["devices"] and verbose:
            print("  ❌ No devices found in this audio effect chain")
        
        rack_info["chains"].append(chain_info)
    
    # Process Audio Effect Group devices (when no branches exist, devices are in the main group)
    for i, audio_group in enumerate(audio_effect_groups):
        # Check if this group has nested branches or is a flat device chain
        branches = audio_group.find("Branches")
        
        if branches is not None and len(branches) == 0:
            # This is a flat Audio Effect Rack (no parallel chains)
            chain_name = "Main Chain"
            user_name_elem = audio_group.find("UserName")
            if user_name_elem is not None:
                user_name = user_name_elem.get("Value", "")
                if user_name:
                    chain_name = user_name
            
            if verbose:
                print(f"\n📁 Audio Effect Chain: {chain_name}")
            
            chain_info = {
                "name": chain_name,
                "is_soloed": False,
                "devices": []
            }
            
            # Find devices directly in the audio group
            devices_found = parse_devices_in_group(audio_group, verbose, 0)
            chain_info["devices"].extend(devices_found)
            
            if not chain_info["devices"] and verbose:
                print("  ❌ No devices found in this audio effect chain")
            
            rack_info["chains"].append(chain_info)
    
    return rack_info

def parse_nested_rack_chains(rack_element, verbose=False, depth=0):
    """Parse chains within a nested rack element"""
    chains = []
    indent = "  " * (depth + 1)
    
    # For AudioEffectGroupDevice, look for branches
    branches = rack_element.find("Branches")
    if branches is not None:
        # Look for individual branch presets within the branches (both Instrument and Audio Effect)
        instrument_branch_presets = branches.findall(".//InstrumentBranchPreset")
        audio_effect_branch_presets = branches.findall(".//AudioEffectBranchPreset")
        
        # Combine both types of branches
        all_branch_presets = instrument_branch_presets + audio_effect_branch_presets
        
        for i, branch in enumerate(all_branch_presets):
            # For AudioEffectBranchPreset, use UserName; for InstrumentBranchPreset, use Name
            if branch.tag == "AudioEffectBranchPreset":
                name_elem = branch.find("UserName")
            else:
                name_elem = branch.find("Name")
            chain_name = name_elem.get("Value") if name_elem is not None else f"Chain {i+1}"
            
            # Check if chain is soloed
            solo_elem = branch.find("IsSoloed")
            is_soloed = solo_elem.get("Value") == "true" if solo_elem is not None else False
            
            if verbose:
                print(f"{indent}📁 Nested Chain: {chain_name} {'(SOLOED)' if is_soloed else ''}")
            
            chain_info = {
                "name": chain_name,
                "is_soloed": is_soloed,
                "devices": []
            }
            
            # Find devices in this nested chain
            device_presets = branch.findall(".//DevicePresets")
            for device_preset_group in device_presets:
                devices_found = parse_devices_in_group(device_preset_group, verbose, depth + 1)
                chain_info["devices"].extend(devices_found)
            
            chains.append(chain_info)
    else:
        # If no branches, this might be a flat rack - treat as single chain
        chain_info = {
            "name": "Main Chain",
            "is_soloed": False,
            "devices": []
        }
        
        # Find devices directly in the rack
        devices_found = parse_devices_in_group(rack_element, verbose, depth + 1)
        chain_info["devices"].extend(devices_found)
        
        if chain_info["devices"]:  # Only add if we found devices
            chains.append(chain_info)
    
    return chains

def parse_devices_in_group(device_group, verbose=False, depth=0):
    """Parse devices within a device group (works for both Instrument and Audio Effect racks)
    
    Args:
        device_group: The XML element containing devices
        verbose: Whether to print verbose output
        depth: Current nesting depth (for recursive calls)
    """
    devices_found = []
    indent = "  " * (depth + 1)  # Indentation for nested output
    
    # First, look for nested racks within this group
    nested_audio_racks = device_group.findall(".//AudioEffectGroupDevice")
    nested_instrument_racks = device_group.findall(".//InstrumentBranchPreset")
    
    # Process nested Audio Effect Racks
    for nested_rack in nested_audio_racks:
        # Skip if this is the same element as the parent (avoid self-reference)
        if nested_rack == device_group:
            continue
            
        user_name_elem = nested_rack.find("UserName")
        rack_name = user_name_elem.get("Value") if user_name_elem is not None else "Nested Audio Rack"
        
        # Check if device is on
        on_elem = nested_rack.find("On/Manual")
        is_on = on_elem.get("Value") == "true" if on_elem is not None else True
        
        if verbose:
            print(f"{indent}🎛️  {rack_name} (Nested Audio Effect Rack) - {'ON' if is_on else 'OFF'}")
        
        # Parse the nested rack's chains recursively
        nested_chains = parse_nested_rack_chains(nested_rack, verbose, depth + 1)
        
        device_info = {
            "type": "AudioEffectGroupDevice",
            "name": rack_name,
            "is_on": is_on,
            "chains": nested_chains
        }
        devices_found.append(device_info)
    
    # Process nested Instrument Racks
    for nested_rack in nested_instrument_racks:
        # Skip if this is the same element as the parent
        if nested_rack == device_group:
            continue
            
        name_elem = nested_rack.find("Name")
        rack_name = name_elem.get("Value") if name_elem is not None else "Nested Instrument Rack"
        
        # Check if device is on
        on_elem = nested_rack.find("On/Manual")
        is_on = on_elem.get("Value") == "true" if on_elem is not None else True
        
        if verbose:
            print(f"{indent}🎹 {rack_name} (Nested Instrument Rack) - {'ON' if is_on else 'OFF'}")
        
        # Parse the nested rack's chains recursively
        nested_chains = parse_nested_rack_chains(nested_rack, verbose, depth + 1)
        
        device_info = {
            "type": "InstrumentBranchPreset",
            "name": rack_name,
            "is_on": is_on,
            "chains": nested_chains
        }
        devices_found.append(device_info)
    
    # Now look for regular devices (excluding nested racks we already processed)
    # 1. Operator devices
    operators = device_group.findall(".//Operator")
    for op in operators:
        # Skip if this operator is inside a nested rack we already processed
        if any(nested_rack in [parent for parent in op.iter()] for nested_rack in nested_audio_racks + nested_instrument_racks):
            continue
            
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
        if verbose:
            print(f"{indent}🎹 {device_name} (Operator) - {'ON' if is_on else 'OFF'}")
    
    # 2. EQ8 devices
    eq8_devices = device_group.findall(".//Eq8")
    for eq in eq8_devices:
        # Skip if this EQ is inside a nested rack we already processed
        if any(nested_rack in [parent for parent in eq.iter()] for nested_rack in nested_audio_racks + nested_instrument_racks):
            continue
            
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
        if verbose:
            print(f"{indent}🎛️  {device_name} (EQ Eight) - {'ON' if is_on else 'OFF'}")
    
    # 3. Look for other Ableton devices by tag name
    common_devices = ['Compressor2', 'AutoFilter', 'Reverb', 'Delay', 'Chorus', 
                    'Phaser', 'AutoPan', 'Gate', 'Limiter', 'MultibandDynamics',
                    'Saturator', 'Frequency', 'Vocoder', 'Bass', 'DrumRack', 
                    'Collision', 'Tension', 'Impulse', 'Simpler', 'Wavetable',
                    'GlueCompressor', 'Shifter', 'PhaserNew', 'StereoGain',
                    'AudioBranchMixerDevice', 'MxDeviceAudioEffect', 'Eq3',
                    'BeatRepeat', 'Flanger', 'Tube']
    
    for device_type in common_devices:
        devices = device_group.findall(f".//{device_type}")
        for device in devices:
            # Skip if this device is inside a nested rack we already processed
            if any(nested_rack in [parent for parent in device.iter()] for nested_rack in nested_audio_racks + nested_instrument_racks):
                continue
                
            user_name_elem = device.find("UserName")
            user_name = user_name_elem.get("Value") if user_name_elem is not None else ""
            # Use device type as primary name, add preset name if available
            if user_name and user_name != device_type:
                device_name = f"{device_type} ({user_name})"
            else:
                device_name = device_type
            
            # Check if device is on
            on_elem = device.find("On/Manual")
            is_on = on_elem.get("Value") == "true" if on_elem is not None else True
            
            device_info = {
                "type": device_type,
                "name": device_name,
                "is_on": is_on
            }
            devices_found.append(device_info)
            if verbose:
                # Add emoji based on device type
                emoji = get_device_emoji(device_type)
                print(f"{indent}{emoji} {device_name} ({device_type}) - {'ON' if is_on else 'OFF'}")
    
    return devices_found

def get_device_emoji(device_type):
    """Return an appropriate emoji for the device type"""
    emoji_map = {
        'MultibandDynamics': '🎚️',
        'Saturator': '🔥',
        'Delay': '🔄',
        'Reverb': '🌊',
        'AutoFilter': '🎛️',
        'Frequency': '📊',
        'GlueCompressor': '🗜️',
        'Shifter': '↕️',
        'PhaserNew': '🌀',
        'StereoGain': '🔊',
        'AudioBranchMixerDevice': '🎚️',
        'MxDeviceAudioEffect': '⚡',
        'Compressor2': '🗜️',
        'Chorus': '🌊',
        'Gate': '🚪',
        'Limiter': '🛡️'
    }
    return emoji_map.get(device_type, '🎛️')

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
        
        print(f"📊 Analysis exported to: {output_file}")
        return output_file
        
    except Exception as e:
        print(f"❌ Error exporting analysis: {e}")
        return None

def print_summary(rack_info, quiet=False):
    """Print a summary of the rack structure"""
    if not rack_info:
        return
    
    if not quiet:
        print(f"\n{'='*60}")
        print("📋 RACK ANALYSIS SUMMARY")
        print(f"{'='*60}")
    
    print(f"🎯 Use Case: {rack_info['use_case']}")
    
    print(f"\n🎛️  Named Macro Controls: {len(rack_info['macro_controls'])}")
    for macro in rack_info['macro_controls']:
        print(f"   • {macro['name']}: {macro['value']}")
    
    print(f"\n🔗 Chains: {len(rack_info['chains'])}")
    total_devices = 0
    
    for chain in rack_info['chains']:
        chain_device_count = count_devices_in_chain(chain)
        total_devices += chain_device_count
        
        chain_display = f"📁 {chain['name']}" if chain['name'] else "📁 [Unnamed Chain]"
        if chain.get('is_soloed', False):
            chain_display += " (SOLOED)"
        print(f"\n{chain_display}")
        print(f"   Devices: {chain_device_count}")
        
        if not quiet:
            print_devices_recursive(chain['devices'], indent="   ")
    
    print(f"\n📊 Total Devices Across All Chains: {total_devices}")

def count_devices_in_chain(chain):
    """Recursively count all devices in a chain, including nested racks"""
    count = 0
    for device in chain['devices']:
        count += 1
        # If device has nested chains, count devices in those too
        if 'chains' in device:
            for nested_chain in device['chains']:
                count += count_devices_in_chain(nested_chain)
    return count

def print_devices_recursive(devices, indent="   "):
    """Recursively print devices, including nested racks"""
    for device in devices:
        status = "🟢" if device['is_on'] else "🔴"
        emoji = get_device_emoji(device['type'])
        print(f"{indent}{status} {emoji} {device['name']} ({device['type']})")
        
        # If this device has nested chains, print them too
        if 'chains' in device:
            for nested_chain in device['chains']:
                chain_display = f"📁 {nested_chain['name']}" if nested_chain['name'] else "📁 [Unnamed Chain]"
                if nested_chain.get('is_soloed', False):
                    chain_display += " (SOLOED)"
                print(f"{indent}  {chain_display}")
                print_devices_recursive(nested_chain['devices'], indent + "    ")

def analyze_ableton_rack(file_path, export_xml=True, export_json=True, output_folder=".", verbose=False, quiet=False):
    """
    Main function to decompress, parse, and analyze an Ableton rack file.
    
    Args:
        file_path (str): Path to the .adg or .adv file
        export_xml (bool): Whether to export the decompressed XML
        export_json (bool): Whether to export the analysis as JSON
        output_folder (str): Folder to save exported files
        verbose (bool): Show detailed device information during analysis
        quiet (bool): Minimal output (summary only)
    
    Returns:
        dict: The rack analysis information, or None if failed
    """
    if not quiet:
        file_name = os.path.basename(file_path)
        print(f"🔍 Analyzing Ableton rack: {file_name}")
        print("=" * 60)
    
    # Step 1: Decompress and parse XML
    xml_root = decompress_and_parse_ableton_file(file_path)
    
    if xml_root is None:
        print(f"❌ Failed to decompress and parse: {os.path.basename(file_path)}")
        return None
    
    if not quiet:
        print(f"✅ Successfully decompressed and parsed: {file_path}")
    
    # Step 2: Export XML if requested
    if export_xml:
        export_xml_to_file(xml_root, file_path, output_folder)
    
    # Step 3: Analyze chains and devices
    rack_info = parse_chains_and_devices(xml_root, file_path, verbose=verbose and not quiet)
    
    if rack_info is None:
        print(f"❌ Failed to analyze rack structure: {os.path.basename(file_path)}")
        return None
    
    # Step 4: Print summary
    print_summary(rack_info, quiet=quiet)
    
    # Step 5: Export JSON analysis if requested
    if export_json:
        export_analysis_to_json(rack_info, file_path, output_folder)
    
    return rack_info

def validate_file_path(file_path):
    """Validate the input file path"""
    if not os.path.exists(file_path):
        print(f"❌ Error: File does not exist: {file_path}")
        return False
    
    if not file_path.lower().endswith(('.adg', '.adv')):
        print(f"❌ Error: File must be an Ableton rack file (.adg or .adv): {file_path}")
        return False
    
    return True

def create_output_directory(output_dir):
    """Create output directory if it doesn't exist"""
    try:
        os.makedirs(output_dir, exist_ok=True)
        return True
    except Exception as e:
        print(f"❌ Error creating output directory: {e}")
        return False

# Example usage
if __name__ == "__main__":
    # Example rack file path - update this to point to your rack files
    rack_file = "/path/to/your/rack.adg"
    
    # Validate the file path
    if validate_file_path(rack_file):
        # Create output directory
        output_dir = "analysis_output"
        if create_output_directory(output_dir):
            # Analyze the rack with enhanced features
            analysis = analyze_ableton_rack(
                file_path=rack_file,
                export_xml=True,      # Export decompressed XML
                export_json=True,     # Export JSON analysis
                output_folder=output_dir,
                verbose=True,         # Show detailed device info
                quiet=False           # Full output
            )
            
            if analysis:
                print(f"\n✅ Analysis complete! Check the exported files in: {output_dir}")
                print(f"📊 Found {len(analysis['chains'])} chains with {sum(len(chain['devices']) for chain in analysis['chains'])} total devices")
            else:
                print(f"\n❌ Analysis failed.")
        else:
            print("❌ Failed to create output directory")
    else:
        print("❌ Invalid file path. Please check the file exists and is a .adg or .adv file.")
        print("\n💡 Usage example:")
        print("   1. Update the 'rack_file' variable above with your rack file path")
        print("   2. Run: python3 abletonRackAnalyzer.py")
        print("   3. Or use the CLI version: python3 abltonRackAnalyzerCLI.py your_rack.adg")
