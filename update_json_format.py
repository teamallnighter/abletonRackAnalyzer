#!/usr/bin/env python3
"""
Script to update existing JSON analysis files to the new format:
- Remove ableton_version and creator fields
- Add use_case field based on filename
"""

import json
import os
import glob

def update_json_file(json_file_path):
    """Update a single JSON file to the new format"""
    try:
        # Read the existing JSON
        with open(json_file_path, 'r') as f:
            data = json.load(f)
        
        # Extract use case from filename
        # Remove the '_analysis.json' suffix and use the remaining name
        base_name = os.path.basename(json_file_path)
        if base_name.endswith('_analysis.json'):
            use_case = base_name[:-13]  # Remove '_analysis.json'
        else:
            use_case = os.path.splitext(base_name)[0]
        
        # Clean up trailing underscore if present
        use_case = use_case.rstrip('_')
        
        # Update the data structure
        updated_data = {
            "rack_name": data.get("rack_name", "Unknown"),
            "use_case": use_case,
            "macro_controls": data.get("macro_controls", []),
            "chains": data.get("chains", [])
        }
        
        # Write the updated JSON back
        with open(json_file_path, 'w') as f:
            json.dump(updated_data, f, indent=2)
        
        print(f"✅ Updated: {os.path.basename(json_file_path)}")
        return True
        
    except Exception as e:
        print(f"❌ Error updating {json_file_path}: {e}")
        return False

def main():
    # Find all JSON analysis files in batch_out directory
    json_files = glob.glob("batch_out/*_analysis.json")
    
    if not json_files:
        print("❌ No JSON analysis files found in batch_out directory")
        return
    
    print(f"🔍 Found {len(json_files)} JSON files to update")
    print("=" * 60)
    
    successful = 0
    failed = 0
    
    for json_file in sorted(json_files):
        if update_json_file(json_file):
            successful += 1
        else:
            failed += 1
    
    print("=" * 60)
    print(f"📊 Update Summary:")
    print(f"✅ Successfully updated: {successful} files")
    if failed > 0:
        print(f"❌ Failed: {failed} files")
    else:
        print("🎉 All files updated successfully!")

if __name__ == "__main__":
    main()
