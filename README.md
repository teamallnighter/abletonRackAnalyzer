# Ableton Rack Analysis Tool

This Python script is designed to help musicians and audio engineers analyze Ableton Live rack files, specifically `.adg` and `.adv` files, which are compressed files containing XML data describing racks, chains, and devices. The tool decompresses these files, parses their XML content, extracts detailed information about macro controls, chains, and devices, and exports this data for further analysis.

---

## Features

- **Decompress and parse** Ableton `.adg` and `.adv` files.
- **Extract macro controls**, chains, and device configurations.
- **Export** the parsed XML to a human-readable XML file.
- **Generate a JSON report** summarizing the rack structure.
- **Print a summary** of the rack, including devices and chain details.

---

## Requirements

- Python 3.x
- Built-in modules: `gzip`, `os`, `json`, `xml.etree.ElementTree`

---

## Usage

1. **Specify your Ableton rack file**

Update the `rack_file` variable in the `if __name__ == "__main__"` section with the path to your `.adg` or `.adv` file.

```python
rack_file = "/path/to/your/rack/file.adg"
```

2. **Run the script**

Execute the script from the command line:

```bash
python ableton_rack_analysis.py
```

3. **Output**

- XML and JSON files will be generated in the specified output folder.
- The console will display a structured summary of the rack's macro controls, chains, and devices.

---

## Functions

### `decompress_and_parse_ableton_file(file_path)`
Decompresses a `.adg` or `.adv` file and returns its XML root element.

- **Arguments:**
  - `file_path` (str): Path to the Ableton rack file.
- **Returns:**
  - `xml.etree.ElementTree.Element`: Root of the parsed XML tree, or `None` if an error occurs.

### `export_xml_to_file(xml_root, original_file_path, output_folder=".")`
Exports the provided XML content to a formatted `.xml` file.

- **Arguments:**
  - `xml_root`: XML root element.
  - `original_file_path` (str): Original rack file path.
  - `output_folder` (str): Folder to save the XML file.
- **Returns:**
  - Path to the exported XML file or `None` if failed.

### `parse_chains_and_devices(xml_root)`
Parses the XML to extract rack configuration: macro controls, chains, and devices.

- **Arguments:**
  - `xml_root`: XML root element.
- **Returns:**
  - Dictionary containing rack info, including macros, chains, and devices.

### `export_analysis_to_json(rack_info, original_file_path, output_folder=".")`
Exports the analyzed rack structure to a JSON file.

- **Arguments:**
  - `rack_info`: The dictionary with parsed rack info.
  - `original_file_path` (str): Original rack file path.
  - `output_folder` (str): Folder to save the JSON file.
- **Returns:**
  - Path to the JSON report or `None` if failed.

### `print_summary(rack_info)`
Displays a readable summary of the rack analysis on the console.

- **Arguments:**
  - `rack_info`: Dictionary with the parsed rack data.

### `analyze_ableton_rack(file_path, export_xml=True, export_json=True, output_folder=".")`
Main function to orchestrate decompression, parsing, analysis, and exporting.

- **Arguments:**
  - `file_path` (str): Path to rack file.
  - `export_xml` (bool): Whether to export parsed XML.
  - `export_json` (bool): Whether to export JSON analysis.
  - `output_folder` (str): Destination folder for exported files.
- **Returns:**
  - Dictionary with rack analysis, or `None` on failure.

---

## Example

```python
if __name__ == "__main__":
    rack_file = "/path/to/your/file.adg"
    analyze_ableton_rack(
        file_path=rack_file,
        export_xml=True,
        export_json=True,
        output_folder="."
    )
```

---

## Notes

- The script is configured to analyze a specific file path by default. Update the file path to your target rack file.
- The tools print detailed information to the console, making it easy to understand the rack configuration.
- Exported files (`.xml` and `_analysis.json`) provide a structured view of the rack for further inspection.

---

## License

This script is provided "as-is" without warranty. Use it freely for personal or educational purposes.

---

Feel free to extend this tool with additional features such as GUI, deeper device analysis, or integration into larger workflows.