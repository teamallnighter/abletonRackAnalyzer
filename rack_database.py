#!/usr/bin/env python3
"""
Rack Database API - Practical web application structure
"""

import json
import sqlite3
from pathlib import Path
from datetime import datetime

class RackDatabase:
    def __init__(self, db_path="racks.db", json_folder="alltheracks_analysis"):
        self.db_path = db_path
        self.json_folder = Path(json_folder)
        self.init_database()
        self.populate_from_json()
    
    def init_database(self):
        """Initialize SQLite database with rack data structure"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS racks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                use_case TEXT UNIQUE,
                category TEXT,
                total_devices INTEGER,
                total_chains INTEGER,
                active_macros INTEGER,
                complexity_score INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS devices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rack_id INTEGER,
                chain_name TEXT,
                device_type TEXT,
                device_name TEXT,
                is_on BOOLEAN,
                position INTEGER,
                FOREIGN KEY (rack_id) REFERENCES racks (id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS macro_controls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rack_id INTEGER,
                name TEXT,
                value REAL,
                index_position INTEGER,
                FOREIGN KEY (rack_id) REFERENCES racks (id)
            )
        ''')
        
        # Create indexes for better performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_device_type ON devices (device_type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_category ON racks (category)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_complexity ON racks (complexity_score)')
        
        conn.commit()
        conn.close()
    
    def populate_from_json(self):
        """Populate database from JSON files"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Clear existing data
        cursor.execute('DELETE FROM macro_controls')
        cursor.execute('DELETE FROM devices')
        cursor.execute('DELETE FROM racks')
        
        json_files = list(self.json_folder.glob("*_analysis.json"))
        
        for file_path in json_files:
            try:
                with open(file_path, 'r') as f:
                    rack_data = json.load(f)
                
                # Extract category from use_case
                use_case = rack_data.get('use_case', 'Unknown')
                category = use_case.split(' - ')[0] if ' - ' in use_case else use_case.split()[0]
                
                # Calculate metrics
                total_devices = sum(len(chain.get('devices', [])) for chain in rack_data.get('chains', []))
                total_chains = len(rack_data.get('chains', []))
                active_macros = len([m for m in rack_data.get('macro_controls', []) if m.get('name', '').strip()])
                complexity_score = total_devices + (active_macros * 2)
                
                # Insert rack
                cursor.execute('''
                    INSERT INTO racks (use_case, category, total_devices, total_chains, active_macros, complexity_score)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (use_case, category, total_devices, total_chains, active_macros, complexity_score))
                
                rack_id = cursor.lastrowid
                
                # Insert devices
                for chain in rack_data.get('chains', []):
                    chain_name = chain.get('name', 'Unknown')
                    for position, device in enumerate(chain.get('devices', [])):
                        cursor.execute('''
                            INSERT INTO devices (rack_id, chain_name, device_type, device_name, is_on, position)
                            VALUES (?, ?, ?, ?, ?, ?)
                        ''', (rack_id, chain_name, device['type'], device.get('name', ''), device.get('is_on', True), position))
                
                # Insert macro controls
                for macro in rack_data.get('macro_controls', []):
                    cursor.execute('''
                        INSERT INTO macro_controls (rack_id, name, value, index_position)
                        VALUES (?, ?, ?, ?)
                    ''', (rack_id, macro.get('name', ''), macro.get('value', 0.0), macro.get('index', 0)))
                
            except Exception as e:
                print(f"Error processing {file_path}: {e}")
        
        conn.commit()
        conn.close()
        print(f"Database populated with {len(json_files)} racks")
    
    def search_racks(self, **filters):
        """Search racks with various filters"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = "SELECT * FROM racks WHERE 1=1"
        params = []
        
        if 'category' in filters:
            query += " AND category LIKE ?"
            params.append(f"%{filters['category']}%")
        
        if 'min_devices' in filters:
            query += " AND total_devices >= ?"
            params.append(filters['min_devices'])
        
        if 'max_devices' in filters:
            query += " AND total_devices <= ?"
            params.append(filters['max_devices'])
        
        if 'device_type' in filters:
            query += " AND id IN (SELECT DISTINCT rack_id FROM devices WHERE device_type = ?)"
            params.append(filters['device_type'])
        
        if 'macro_name' in filters:
            query += " AND id IN (SELECT DISTINCT rack_id FROM macro_controls WHERE name LIKE ?)"
            params.append(f"%{filters['macro_name']}%")
        
        query += " ORDER BY complexity_score DESC"
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        conn.close()
        
        # Convert to dictionaries
        columns = ['id', 'use_case', 'category', 'total_devices', 'total_chains', 'active_macros', 'complexity_score', 'created_at']
        return [dict(zip(columns, row)) for row in results]
    
    def get_rack_details(self, rack_id):
        """Get full details for a specific rack"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get rack info
        cursor.execute("SELECT * FROM racks WHERE id = ?", (rack_id,))
        rack = cursor.fetchone()
        
        if not rack:
            return None
        
        # Get devices
        cursor.execute("""
            SELECT chain_name, device_type, device_name, is_on, position 
            FROM devices 
            WHERE rack_id = ? 
            ORDER BY chain_name, position
        """, (rack_id,))
        devices = cursor.fetchall()
        
        # Get macros
        cursor.execute("""
            SELECT name, value, index_position 
            FROM macro_controls 
            WHERE rack_id = ? 
            ORDER BY index_position
        """, (rack_id,))
        macros = cursor.fetchall()
        
        conn.close()
        
        return {
            'rack': rack,
            'devices': devices,
            'macros': macros
        }
    
    def get_statistics(self):
        """Get database statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        stats = {}
        
        # Basic counts
        cursor.execute("SELECT COUNT(*) FROM racks")
        stats['total_racks'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM devices")
        stats['total_devices'] = cursor.fetchone()[0]
        
        # Most popular devices
        cursor.execute("""
            SELECT device_type, COUNT(*) as count 
            FROM devices 
            GROUP BY device_type 
            ORDER BY count DESC 
            LIMIT 10
        """)
        stats['popular_devices'] = cursor.fetchall()
        
        # Category distribution
        cursor.execute("""
            SELECT category, COUNT(*) as count 
            FROM racks 
            GROUP BY category 
            ORDER BY count DESC
        """)
        stats['category_distribution'] = cursor.fetchall()
        
        # Complexity distribution
        cursor.execute("""
            SELECT 
                AVG(complexity_score) as avg_complexity,
                MIN(complexity_score) as min_complexity,
                MAX(complexity_score) as max_complexity
            FROM racks
        """)
        complexity = cursor.fetchone()
        stats['complexity_stats'] = {
            'average': complexity[0],
            'minimum': complexity[1],
            'maximum': complexity[2]
        }
        
        conn.close()
        return stats

def demo_database():
    """Demonstrate database functionality"""
    print("\n🗄️  RACK DATABASE DEMO")
    print("="*40)
    
    db = RackDatabase()
    
    # Show statistics
    stats = db.get_statistics()
    print(f"\n📊 Database Statistics:")
    print(f"   Total Racks: {stats['total_racks']}")
    print(f"   Total Device Instances: {stats['total_devices']}")
    print(f"   Average Complexity: {stats['complexity_stats']['average']:.1f}")
    
    # Search examples
    print(f"\n🔍 Search Examples:")
    
    # Find channel strips
    channel_strips = db.search_racks(category="Channel")
    print(f"   Channel Strips: {len(channel_strips)} found")
    
    # Find racks with compressors
    compressor_racks = db.search_racks(device_type="Compressor2")
    print(f"   Racks with Compressor2: {len(compressor_racks)} found")
    
    # Find complex racks
    complex_racks = db.search_racks(min_devices=20)
    print(f"   Complex racks (20+ devices): {len(complex_racks)} found")
    
    # Show top categories
    print(f"\n📂 Top Categories:")
    for category, count in stats['category_distribution'][:5]:
        print(f"   {category}: {count} racks")

if __name__ == "__main__":
    demo_database()
