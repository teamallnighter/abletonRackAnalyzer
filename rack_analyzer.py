#!/usr/bin/env python3
"""
Rack Data Analyzer - Extract insights from Ableton rack JSON data
"""

import json
import os
from collections import Counter, defaultdict
from pathlib import Path

class RackAnalyzer:
    def __init__(self, json_folder_path):
        self.json_folder = Path(json_folder_path)
        self.racks = []
        self.load_rack_data()
    
    def load_rack_data(self):
        """Load all JSON rack files"""
        json_files = list(self.json_folder.glob("*_analysis.json"))
        print(f"Found {len(json_files)} rack files")
        
        for file_path in json_files:
            try:
                with open(file_path, 'r') as f:
                    rack_data = json.load(f)
                    self.racks.append(rack_data)
            except Exception as e:
                print(f"Error loading {file_path}: {e}")
        
        print(f"Successfully loaded {len(self.racks)} racks")
    
    def analyze_device_popularity(self):
        """Find most popular devices across all racks"""
        device_counter = Counter()
        
        for rack in self.racks:
            for chain in rack.get('chains', []):
                for device in chain.get('devices', []):
                    device_counter[device['type']] += 1
        
        return device_counter.most_common()
    
    def analyze_device_combinations(self):
        """Find common device combinations"""
        combinations = Counter()
        
        for rack in self.racks:
            for chain in rack.get('chains', []):
                devices = [d['type'] for d in chain.get('devices', [])]
                # Look at 2-device combinations
                for i in range(len(devices) - 1):
                    combo = f"{devices[i]} → {devices[i+1]}"
                    combinations[combo] += 1
        
        return combinations.most_common(20)
    
    def analyze_complexity_by_category(self):
        """Analyze rack complexity by use case category"""
        category_stats = defaultdict(list)
        
        for rack in self.racks:
            use_case = rack.get('use_case', 'Unknown')
            category = use_case.split(' - ')[0] if ' - ' in use_case else use_case.split()[0]
            
            total_devices = sum(len(chain.get('devices', [])) for chain in rack.get('chains', []))
            category_stats[category].append(total_devices)
        
        # Calculate averages
        category_averages = {}
        for category, device_counts in category_stats.items():
            if device_counts:  # Avoid division by zero
                category_averages[category] = {
                    'avg_devices': sum(device_counts) / len(device_counts),
                    'max_devices': max(device_counts),
                    'min_devices': min(device_counts),
                    'rack_count': len(device_counts)
                }
        
        return category_averages
    
    def analyze_macro_patterns(self):
        """Analyze macro control naming patterns"""
        macro_names = Counter()
        empty_macros = 0
        total_macros = 0
        
        for rack in self.racks:
            for macro in rack.get('macro_controls', []):
                total_macros += 1
                name = macro.get('name', '').strip()
                if name:
                    macro_names[name] += 1
                else:
                    empty_macros += 1
        
        return {
            'most_common_names': macro_names.most_common(20),
            'empty_macro_percentage': (empty_macros / total_macros * 100) if total_macros > 0 else 0,
            'total_macros': total_macros
        }
    
    def find_racks_with_device(self, device_type):
        """Find all racks containing a specific device"""
        matching_racks = []
        
        for rack in self.racks:
            for chain in rack.get('chains', []):
                for device in chain.get('devices', []):
                    if device['type'] == device_type:
                        matching_racks.append({
                            'use_case': rack.get('use_case'),
                            'chain_name': chain.get('name'),
                            'total_devices': len(chain.get('devices', []))
                        })
                        break
        
        return matching_racks
    
    def generate_report(self):
        """Generate comprehensive analysis report"""
        print("\n" + "="*60)
        print("🎛️  ABLETON RACK ANALYSIS REPORT")
        print("="*60)
        
        print(f"\n📊 Dataset Overview:")
        print(f"   Total Racks Analyzed: {len(self.racks)}")
        
        # Device popularity
        print(f"\n🏆 Most Popular Devices:")
        device_popularity = self.analyze_device_popularity()
        for i, (device, count) in enumerate(device_popularity[:10], 1):
            print(f"   {i:2d}. {device}: {count} racks")
        
        # Device combinations
        print(f"\n🔗 Common Device Combinations:")
        combinations = self.analyze_device_combinations()
        for i, (combo, count) in enumerate(combinations[:5], 1):
            print(f"   {i}. {combo}: {count} times")
        
        # Complexity by category
        print(f"\n📈 Complexity by Category:")
        complexity = self.analyze_complexity_by_category()
        sorted_complexity = sorted(complexity.items(), key=lambda x: x[1]['avg_devices'], reverse=True)
        for category, stats in sorted_complexity[:10]:
            print(f"   {category}: {stats['avg_devices']:.1f} avg devices ({stats['rack_count']} racks)")
        
        # Macro patterns
        print(f"\n🎚️  Macro Control Patterns:")
        macro_analysis = self.analyze_macro_patterns()
        print(f"   Empty macros: {macro_analysis['empty_macro_percentage']:.1f}%")
        print(f"   Most common macro names:")
        for name, count in macro_analysis['most_common_names'][:5]:
            print(f"     '{name}': {count} times")

if __name__ == "__main__":
    # Run analysis on the generated rack data
    analyzer = RackAnalyzer("alltheracks_analysis")
    analyzer.generate_report()
    
    # Example specific queries
    print(f"\n🔍 Example Queries:")
    reverb_racks = analyzer.find_racks_with_device('Reverb')
    print(f"   Racks with Reverb: {len(reverb_racks)}")
    
    compressor_racks = analyzer.find_racks_with_device('Compressor2')
    print(f"   Racks with Compressor2: {len(compressor_racks)}")
