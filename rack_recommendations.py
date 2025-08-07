#!/usr/bin/env python3
"""
Rack Recommendation Engine - Practical applications of the rack data
"""

import json
from pathlib import Path
from collections import defaultdict
import random

# Import the analyzer class
from rack_analyzer import RackAnalyzer

class RackRecommendationEngine:
    def __init__(self, json_folder_path):
        self.analyzer = RackAnalyzer(json_folder_path)
    
    def recommend_similar_racks(self, target_use_case, limit=5):
        """Recommend racks similar to a given use case"""
        target_rack = None
        for rack in self.analyzer.racks:
            if rack['use_case'] == target_use_case:
                target_rack = rack
                break
        
        if not target_rack:
            return f"Rack '{target_use_case}' not found"
        
        # Get devices from target rack
        target_devices = set()
        for chain in target_rack.get('chains', []):
            for device in chain.get('devices', []):
                target_devices.add(device['type'])
        
        # Find racks with similar devices
        similar_racks = []
        for rack in self.analyzer.racks:
            if rack['use_case'] == target_use_case:
                continue
                
            rack_devices = set()
            for chain in rack.get('chains', []):
                for device in chain.get('devices', []):
                    rack_devices.add(device['type'])
            
            # Calculate similarity (Jaccard index)
            if target_devices and rack_devices:
                intersection = len(target_devices & rack_devices)
                union = len(target_devices | rack_devices)
                similarity = intersection / union
                
                if similarity > 0:
                    similar_racks.append({
                        'use_case': rack['use_case'],
                        'similarity': similarity,
                        'shared_devices': list(target_devices & rack_devices),
                        'device_count': sum(len(chain.get('devices', [])) for chain in rack.get('chains', []))
                    })
        
        # Sort by similarity and return top results
        similar_racks.sort(key=lambda x: x['similarity'], reverse=True)
        return similar_racks[:limit]
    
    def find_racks_for_genre(self, genre_keywords):
        """Find racks suitable for a specific genre"""
        matching_racks = []
        
        for rack in self.analyzer.racks:
            use_case = rack['use_case'].lower()
            if any(keyword.lower() in use_case for keyword in genre_keywords):
                device_count = sum(len(chain.get('devices', [])) for chain in rack.get('chains', []))
                matching_racks.append({
                    'use_case': rack['use_case'],
                    'device_count': device_count,
                    'macro_controls': len([m for m in rack.get('macro_controls', []) if m.get('name', '').strip()])
                })
        
        return sorted(matching_racks, key=lambda x: x['device_count'], reverse=True)
    
    def create_learning_path(self, start_simple=True):
        """Create a learning path from simple to complex racks"""
        rack_complexity = []
        
        for rack in self.analyzer.racks:
            device_count = sum(len(chain.get('devices', [])) for chain in rack.get('chains', []))
            macro_count = len([m for m in rack.get('macro_controls', []) if m.get('name', '').strip()])
            
            rack_complexity.append({
                'use_case': rack['use_case'],
                'device_count': device_count,
                'macro_count': macro_count,
                'complexity_score': device_count + (macro_count * 2)  # Weight macros more
            })
        
        # Sort by complexity
        rack_complexity.sort(key=lambda x: x['complexity_score'], reverse=not start_simple)
        
        return rack_complexity
    
    def analyze_device_workflows(self):
        """Analyze common device workflow patterns"""
        workflows = defaultdict(list)
        
        for rack in self.analyzer.racks:
            for chain in rack.get('chains', []):
                devices = [d['type'] for d in chain.get('devices', [])]
                if len(devices) >= 2:
                    # Create workflow signature
                    workflow = " → ".join(devices)
                    workflows[workflow].append(rack['use_case'])
        
        # Find most common workflows
        common_workflows = []
        for workflow, racks in workflows.items():
            if len(racks) >= 2:  # Appears in at least 2 racks
                common_workflows.append({
                    'workflow': workflow,
                    'frequency': len(racks),
                    'example_racks': racks[:3]
                })
        
        return sorted(common_workflows, key=lambda x: x['frequency'], reverse=True)

def main():
    print("\n🎯 RACK RECOMMENDATION ENGINE")
    print("="*50)
    
    engine = RackRecommendationEngine("alltheracks_analysis")
    
    # Example 1: Find similar racks
    print("\n1️⃣ Racks similar to 'Channel Strip - Drumkit Pumpit':")
    similar = engine.recommend_similar_racks("Channel Strip - Drumkit Pumpit")
    if isinstance(similar, list):
        for i, rack in enumerate(similar, 1):
            print(f"   {i}. {rack['use_case']}")
            print(f"      Similarity: {rack['similarity']:.2f}")
            print(f"      Shared devices: {', '.join(rack['shared_devices'])}")
            print()
    else:
        print(f"   {similar}")
    
    # Example 2: Genre-specific racks
    print("\n2️⃣ Racks for Electronic/Dance music:")
    electronic_racks = engine.find_racks_for_genre(['dance', 'electronic', 'beat', 'bass', 'drum'])
    for i, rack in enumerate(electronic_racks[:5], 1):
        print(f"   {i}. {rack['use_case']} ({rack['device_count']} devices)")
    
    # Example 3: Learning path
    print("\n3️⃣ Learning Path (Simple → Complex):")
    learning_path = engine.create_learning_path(start_simple=True)
    print("   Beginner-friendly racks:")
    for rack in learning_path[:3]:
        print(f"     • {rack['use_case']} (Score: {rack['complexity_score']})")
    
    print("\n   Advanced racks:")
    for rack in learning_path[-3:]:
        print(f"     • {rack['use_case']} (Score: {rack['complexity_score']})")
    
    # Example 4: Common workflows
    print("\n4️⃣ Most Common Device Workflows:")
    workflows = engine.analyze_device_workflows()
    for i, workflow in enumerate(workflows[:3], 1):
        print(f"   {i}. {workflow['workflow']}")
        print(f"      Used in {workflow['frequency']} racks")
        print(f"      Examples: {', '.join(workflow['example_racks'])}")
        print()

if __name__ == "__main__":
    main()
