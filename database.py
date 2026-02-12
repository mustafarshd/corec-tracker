"""
Database operations for storing and retrieving facility usage data.
"""
import os
import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Optional


def _default_db_path() -> str:
    """Use a path that is writable on Railway/Heroku (e.g. /tmp)."""
    if os.environ.get("PORT"):
        # Platform sets PORT (Railway, Heroku, etc.) - use /tmp for SQLite
        base = os.environ.get("TMPDIR", "/tmp")
        path = os.path.join(base, "facility_data.db")
        # Ensure parent dir exists (e.g. /tmp)
        parent = os.path.dirname(path)
        if parent and not os.path.isdir(parent):
            try:
                os.makedirs(parent, exist_ok=True)
            except OSError:
                pass
        return path
    return "facility_data.db"


class FacilityDatabase:
    def __init__(self, db_path: str = None):
        self.db_path = db_path or _default_db_path()
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create facilities table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS facilities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create usage_data table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS usage_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                facility_id INTEGER NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                occupancy INTEGER,
                capacity INTEGER,
                percentage REAL,
                metadata TEXT,
                FOREIGN KEY (facility_id) REFERENCES facilities(id),
                UNIQUE(facility_id, timestamp)
            )
        """)
        
        # Create indexes for faster queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_facility_timestamp 
            ON usage_data(facility_id, timestamp)
        """)
        
        conn.commit()
        conn.close()
    
    def get_or_create_facility(self, name: str) -> int:
        """Get facility ID or create if it doesn't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT id FROM facilities WHERE name = ?", (name,))
        result = cursor.fetchone()
        
        if result:
            facility_id = result[0]
        else:
            cursor.execute("INSERT INTO facilities (name) VALUES (?)", (name,))
            facility_id = cursor.lastrowid
        
        conn.commit()
        conn.close()
        return facility_id
    
    def insert_usage_data(self, facility_name: str, timestamp: datetime, 
                         occupancy: Optional[int] = None, 
                         capacity: Optional[int] = None,
                         percentage: Optional[float] = None,
                         metadata: Optional[Dict] = None):
        """Insert facility usage data."""
        facility_id = self.get_or_create_facility(facility_name)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        metadata_json = json.dumps(metadata) if metadata else None
        
        cursor.execute("""
            INSERT OR REPLACE INTO usage_data 
            (facility_id, timestamp, occupancy, capacity, percentage, metadata)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (facility_id, timestamp, occupancy, capacity, percentage, metadata_json))
        
        conn.commit()
        conn.close()
    
    def get_facility_data(self, facility_name: str, 
                         start_date: Optional[datetime] = None,
                         end_date: Optional[datetime] = None) -> List[Dict]:
        """Get historical data for a specific facility."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        facility_id = self.get_or_create_facility(facility_name)
        
        query = """
            SELECT timestamp, occupancy, capacity, percentage, metadata
            FROM usage_data
            WHERE facility_id = ?
        """
        params = [facility_id]
        
        if start_date:
            query += " AND timestamp >= ?"
            params.append(start_date)
        
        if end_date:
            query += " AND timestamp <= ?"
            params.append(end_date)
        
        query += " ORDER BY timestamp"
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        
        conn.close()
        
        return [
            {
                'timestamp': row[0],
                'occupancy': row[1],
                'capacity': row[2],
                'percentage': row[3],
                'metadata': json.loads(row[4]) if row[4] else None
            }
            for row in results
        ]
    
    def get_all_facilities(self) -> List[str]:
        """Get list of all facilities in the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM facilities ORDER BY name")
        results = cursor.fetchall()
        
        conn.close()
        return [row[0] for row in results]
    
    def get_data_by_time_of_day(self, facility_name: str, 
                                days_back: int = 7) -> Dict:
        """Get aggregated data grouped by time of day."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        facility_id = self.get_or_create_facility(facility_name)
        
        # Get data from the last N days
        cursor.execute("""
            SELECT 
                strftime('%H:%M', timestamp) as time_of_day,
                strftime('%w', timestamp) as day_of_week,
                AVG(percentage) as avg_percentage,
                AVG(occupancy) as avg_occupancy,
                COUNT(*) as sample_count
            FROM usage_data
            WHERE facility_id = ?
            AND timestamp >= datetime('now', '-' || ? || ' days')
            GROUP BY time_of_day, day_of_week
            ORDER BY day_of_week, time_of_day
        """, (facility_id, days_back))
        
        results = cursor.fetchall()
        conn.close()
        
        # Organize by day of week and time
        data = {}
        day_names = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 
                    'Thursday', 'Friday', 'Saturday']
        
        for row in results:
            time_of_day = row[0]
            day_of_week = int(row[1])
            avg_percentage = row[2]
            avg_occupancy = row[3]
            sample_count = row[4]
            
            day_name = day_names[day_of_week]
            
            if day_name not in data:
                data[day_name] = {}
            
            data[day_name][time_of_day] = {
                'avg_percentage': avg_percentage,
                'avg_occupancy': avg_occupancy,
                'sample_count': sample_count
            }
        
        return data
