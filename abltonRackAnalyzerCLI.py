#!/usr/bin/env python3
"""
Ableton Rack Analyzer CLI
A command-line tool for analyzing Ableton Live rack files (.adg/.adv)

Usage:
    python rack_analyzer_cli.py <file_path> [options]
    python rack_analyzer_cli.py --help
"""

import argparse
import sys
import os
import gzip
import xml.etree.ElementTree as ET
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
            print(f"\n� Chain: {chain_name} {'(SOLOED)' if is_soloed else ''}")
        
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
        # Look for individual branch presets within the branches
        branch_presets = branches.findall(".//InstrumentBranchPreset")
        for i, branch in enumerate(branch_presets):
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
                    'AudioBranchMixerDevice', 'MxDeviceAudioEffect']
    
    for device_type in common_devices:
        devices = device_group.findall(f".//{device_type}")
        for device in devices:
            # Skip if this device is inside a nested rack we already processed
            if any(nested_rack in [parent for parent in device.iter()] for nested_rack in nested_audio_racks + nested_instrument_racks):
                continue
                
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

def validate_file_path(file_path):
    """Validate the input file path (can be file or directory)"""
    if not os.path.exists(file_path):
        print(f"❌ Error: Path does not exist: {file_path}")
        return False
    
    if os.path.isfile(file_path):
        if not file_path.lower().endswith(('.adg', '.adv')):
            print(f"❌ Error: File must be an Ableton rack file (.adg or .adv): {file_path}")
            return False
    elif os.path.isdir(file_path):
        # Check if directory contains any .adg or .adv files
        rack_files = find_rack_files(file_path)
        if not rack_files:
            print(f"❌ Error: No Ableton rack files (.adg/.adv) found in directory: {file_path}")
            return False
    else:
        print(f"❌ Error: Path is neither a file nor directory: {file_path}")
        return False
    
    return True

def find_rack_files(directory_path, recursive=True):
    """Find all Ableton rack files in a directory"""
    rack_files = []
    
    if recursive:
        # Use os.walk for recursive search
        for root, dirs, files in os.walk(directory_path):
            for file in files:
                if file.lower().endswith(('.adg', '.adv')):
                    rack_files.append(os.path.join(root, file))
    else:
        # Only search in the immediate directory
        for file in os.listdir(directory_path):
            file_path = os.path.join(directory_path, file)
            if os.path.isfile(file_path) and file.lower().endswith(('.adg', '.adv')):
                rack_files.append(file_path)
    
    return sorted(rack_files)

def analyze_single_file(file_path, args):
    """Analyze a single Ableton rack file"""
    if not args.quiet:
        file_name = os.path.basename(file_path)
        print(f"🔍 Analyzing Ableton rack: {file_name}")
        print("=" * 60)
    
    # Step 1: Decompress and parse XML
    xml_root = decompress_and_parse_ableton_file(file_path)
    
    if xml_root is None:
        print(f"❌ Failed to decompress and parse: {os.path.basename(file_path)}")
        return False
    
    if not args.quiet:
        print(f"✅ Successfully decompressed and parsed: {file_path}")
    
    # Step 2: Export XML if requested
    if not args.no_xml:
        export_xml_to_file(xml_root, file_path, args.output)
    
    # Step 3: Analyze chains and devices
    rack_info = parse_chains_and_devices(xml_root, file_path, verbose=args.verbose and not args.quiet)
    
    if rack_info is None:
        print(f"❌ Failed to analyze rack structure: {os.path.basename(file_path)}")
        return False
    
    # Step 4: Print summary
    print_summary(rack_info, quiet=args.quiet)
    
    # Step 5: Export JSON analysis if requested
    if not args.no_json:
        export_analysis_to_json(rack_info, file_path, args.output)
    
    return True

def create_output_directory(output_dir):
    """Create output directory if it doesn't exist"""
    try:
        os.makedirs(output_dir, exist_ok=True)
        return True
    except Exception as e:
        print(f"❌ Error creating output directory: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(
        description="Analyze Ableton Live rack files (.adg/.adv) - supports single files and batch processing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Single File Examples:
  %(prog)s my_rack.adg                    # Basic analysis of single file
  %(prog)s my_rack.adg --verbose          # Detailed output with device info
  %(prog)s my_rack.adg --no-xml           # Skip XML export
  %(prog)s my_rack.adg -o exports/        # Custom output folder
  %(prog)s my_rack.adv --json-only        # Only export JSON analysis

Batch Processing Examples:
  %(prog)s /path/to/racks/                # Analyze all racks in directory tree
  %(prog)s /path/to/racks/ --quiet        # Batch process with minimal output
  %(prog)s /path/to/racks/ --no-recursive # Only process immediate directory
  %(prog)s /path/to/racks/ --json-only    # Batch export JSON only
  %(prog)s /path/to/racks/ -o batch_out/  # Batch with custom output folder
  %(prog)s /path/to/racks/ --no-xml -v    # Batch with verbose, no XML export
        """
    )
    
    # Required arguments
    parser.add_argument(
        'file_path',
        help='Path to an Ableton rack file (.adg/.adv) or directory containing rack files for batch processing'
    )
    
    # Optional arguments
    parser.add_argument(
        '-o', '--output',
        default='.',
        help='Output directory for exported files (default: current directory)'
    )
    
    parser.add_argument(
        '--no-recursive',
        action='store_true',
        help='When processing a directory, only process files in the immediate directory (not subdirectories)'
    )
    
    parser.add_argument(
        '--no-xml',
        action='store_true',
        help='Skip XML export'
    )
    
    parser.add_argument(
        '--no-json',
        action='store_true',
        help='Skip JSON export'
    )
    
    parser.add_argument(
        '--json-only',
        action='store_true',
        help='Only export JSON analysis (skip XML and detailed output)'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Show detailed device information during analysis'
    )
    
    parser.add_argument(
        '-q', '--quiet',
        action='store_true',
        help='Minimal output (summary only)'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='Ableton Rack Analyzer CLI v1.0.0'
    )
    
    try:
        args = parser.parse_args()
    except SystemExit as e:
        # If argument parsing fails, exit gracefully
        sys.exit(e.code)
    
    # Validate inputs
    if not validate_file_path(args.file_path):
        sys.exit(1)
    
    if not create_output_directory(args.output):
        sys.exit(1)
    
    # Handle conflicting options
    if args.quiet and args.verbose:
        print("❌ Error: Cannot use --quiet and --verbose together")
        sys.exit(1)
    
    if args.json_only:
        args.no_xml = True
        args.quiet = True
    
    # Determine if we're processing a single file or directory
    if os.path.isfile(args.file_path):
        # Single file processing
        if not args.quiet:
            file_name = os.path.basename(args.file_path)
            print(f"🔍 Analyzing Ableton rack: {file_name}")
            print("=" * 60)
        
        success = analyze_single_file(args.file_path, args)
        
        if not args.quiet:
            if success:
                print(f"\n✅ Analysis complete!")
            else:
                print(f"\n❌ Analysis failed!")
            if not args.no_xml or not args.no_json:
                print(f"📁 Check the output folder: {os.path.abspath(args.output)}")
    
    elif os.path.isdir(args.file_path):
        # Directory processing
        rack_files = find_rack_files(args.file_path, recursive=not args.no_recursive)
        
        if not rack_files:
            print(f"❌ No Ableton rack files found in: {args.file_path}")
            sys.exit(1)
        
        if not args.quiet:
            search_type = "recursively" if not args.no_recursive else "in directory"
            print(f"📂 Found {len(rack_files)} rack files {search_type}")
            print(f"🔍 Processing directory: {args.file_path}")
            print("=" * 60)
        
        successful = 0
        failed = 0
        
        for i, file_path in enumerate(rack_files, 1):
            if not args.quiet:
                print(f"\n[{i}/{len(rack_files)}] Processing: {os.path.basename(file_path)}")
            
            if analyze_single_file(file_path, args):
                successful += 1
            else:
                failed += 1
            
            # Add separator between files (except for the last one)
            if not args.quiet and i < len(rack_files):
                print("\n" + "-" * 40)
        
        # Final summary for batch processing
        if not args.quiet:
            print(f"\n{'='*60}")
            print("📊 BATCH PROCESSING SUMMARY")
            print(f"{'='*60}")
            print(f"✅ Successfully processed: {successful} files")
            if failed > 0:
                print(f"❌ Failed: {failed} files")
            print(f"📁 All outputs saved to: {os.path.abspath(args.output)}")
        else:
            # Even in quiet mode, show batch summary
            print(f"📊 Batch complete: {successful} successful, {failed} failed")
            if not args.no_xml or not args.no_json:
                print(f"📁 Outputs saved to: {os.path.abspath(args.output)}")

if __name__ == "__main__":
    main()
