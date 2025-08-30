import sqlite3
import numpy as np
import json
import pickle
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import pandas as pd
from tqdm import tqdm

class DatabaseManager:
    def __init__(self, db_path: str = "db/measurements.db"):
        self.db_path = Path(db_path)
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables."""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS measurements (
                    id INTEGER PRIMARY KEY,
                    name TEXT UNIQUE NOT NULL,
                    date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS frames (
                    id INTEGER PRIMARY KEY,
                    measurement_id INTEGER,
                    frame_name TEXT NOT NULL,
                    frame_number INTEGER,
                    FOREIGN KEY (measurement_id) REFERENCES measurements (id),
                    UNIQUE(measurement_id, frame_name)
                );
                
                CREATE TABLE IF NOT EXISTS detections (
                    id INTEGER PRIMARY KEY,
                    frame_id INTEGER,
                    centers BLOB,
                    radii BLOB,
                    statistics TEXT,
                    FOREIGN KEY (frame_id) REFERENCES frames (id)
                );
                
                CREATE TABLE IF NOT EXISTS vector_fields (
                    id INTEGER PRIMARY KEY,
                    measurement_id INTEGER,
                    frame1_id INTEGER,
                    frame2_id INTEGER,
                    source TEXT,
                    x_data BLOB,
                    y_data BLOB,
                    u_data BLOB,
                    v_data BLOB,
                    flags BLOB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (measurement_id) REFERENCES measurements (id),
                    FOREIGN KEY (frame1_id) REFERENCES frames (id),
                    FOREIGN KEY (frame2_id) REFERENCES frames (id)
                );
                
                CREATE INDEX IF NOT EXISTS idx_vector_fields_lookup 
                ON vector_fields(measurement_id, frame1_id, frame2_id, source);
            """)
    
    def _serialize_array(self, arr: np.ndarray) -> bytes:
        """Serialize numpy array to bytes."""
        return pickle.dumps(arr)
    
    def _deserialize_array(self, data: bytes) -> np.ndarray:
        """Deserialize bytes to numpy array."""
        return pickle.loads(data)
    
    def create_measurement(self, name: str) -> int:
        """Create a new measurement and return its ID."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("INSERT OR IGNORE INTO measurements (name) VALUES (?)", (name,))
            if cursor.rowcount == 0:
                # Measurement already exists, get its ID
                cursor = conn.execute("SELECT id FROM measurements WHERE name = ?", (name,))
                return cursor.fetchone()[0]
            return cursor.lastrowid
    
    def create_frame(self, measurement_id: int, frame_name: str) -> int:
        """Create a new frame and return its ID."""
        # Extract frame number from name (e.g., "DSC_0001.jpg" -> 1)
        frame_number = int(frame_name.split('_')[1].split('.')[0])
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "INSERT OR IGNORE INTO frames (measurement_id, frame_name, frame_number) VALUES (?, ?, ?)",
                (measurement_id, frame_name, frame_number)
            )
            if cursor.rowcount == 0:
                # Frame already exists, get its ID
                cursor = conn.execute(
                    "SELECT id FROM frames WHERE measurement_id = ? AND frame_name = ?",
                    (measurement_id, frame_name)
                )
                return cursor.fetchone()[0]
            return cursor.lastrowid
    
    def save_detection_data(self, frame_id: int, centers: np.ndarray, radii: np.ndarray, statistics: dict):
        """Save detection data for a frame."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT OR REPLACE INTO detections 
                   (frame_id, centers, radii, statistics) VALUES (?, ?, ?, ?)""",
                (frame_id, 
                 self._serialize_array(centers),
                 self._serialize_array(radii),
                 json.dumps(statistics))
            )
    
    def save_vector_field(self, measurement_id: int, frame1_id: int, frame2_id: int, 
                         source: str, data: Dict[str, np.ndarray]):
        """Save vector field data."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """INSERT OR REPLACE INTO vector_fields 
                   (measurement_id, frame1_id, frame2_id, source, x_data, y_data, u_data, v_data, flags)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (measurement_id, frame1_id, frame2_id, source,
                 self._serialize_array(data['x']),
                 self._serialize_array(data['y']),
                 self._serialize_array(data['u']),
                 self._serialize_array(data['v']),
                 self._serialize_array(data.get('flags', np.array([]))))
            )
    
    def load_detection_data(self, measurement_name: str) -> pd.DataFrame:
        """Load all detection data for a measurement."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT f.frame_name, d.centers, d.radii, d.statistics
                FROM measurements m
                JOIN frames f ON m.id = f.measurement_id
                JOIN detections d ON f.id = d.frame_id
                WHERE m.name = ?
                ORDER BY f.frame_number
            """, (measurement_name,))
            
            data = []
            for row in cursor.fetchall():
                frame_name, centers_blob, radii_blob, statistics_json = row
                data.append({
                    'frame': frame_name,
                    'centers': self._deserialize_array(centers_blob),
                    'radii': self._deserialize_array(radii_blob),
                    'statistic': json.loads(statistics_json)
                })
            
            return pd.DataFrame(data)
    
    def load_vector_field(self, measurement_name: str, frame1_name: str, 
                         frame2_name: str, source: str) -> Dict[str, np.ndarray]:
        """Load vector field data."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT vf.x_data, vf.y_data, vf.u_data, vf.v_data, vf.flags
                FROM measurements m
                JOIN frames f1 ON m.id = f1.measurement_id
                JOIN frames f2 ON m.id = f2.measurement_id
                JOIN vector_fields vf ON (vf.frame1_id = f1.id AND vf.frame2_id = f2.id)
                WHERE m.name = ? AND f1.frame_name = ? AND f2.frame_name = ? AND vf.source = ?
            """, (measurement_name, frame1_name, frame2_name, source))
            
            row = cursor.fetchone()
            if row is None:
                raise FileNotFoundError(f"Vector field not found for {frame1_name} -> {frame2_name}")
            
            x_data, y_data, u_data, v_data, flags_data = row
            result = {
                'x': self._deserialize_array(x_data),
                'y': self._deserialize_array(y_data),
                'u': self._deserialize_array(u_data),
                'v': self._deserialize_array(v_data)
            }
            
            # Add flags if they exist and are not empty
            flags = self._deserialize_array(flags_data)
            if flags.size > 0:
                result['flags'] = flags
                
            return result
    
    def get_frame_id(self, measurement_name: str, frame_name: str) -> int:
        """Get frame ID by measurement name and frame name."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT f.id FROM measurements m
                JOIN frames f ON m.id = f.measurement_id
                WHERE m.name = ? AND f.frame_name = ?
            """, (measurement_name, frame_name))
            
            result = cursor.fetchone()
            if result is None:
                raise ValueError(f"Frame {frame_name} not found in measurement {measurement_name}")
            return result[0]

    def migration_from_files(self, measure):
        """Migrate existing data from files to database."""
        print(f"Migrating measurement {measure.get_name()} to database...")
        
        # Create measurement
        measurement_id = self.create_measurement(measure.get_name())
        
        # Try to load existing pickle file
        try:
            existing_data = measure.load_pickled_data(source='drive')
            print(f"Found existing pickle data with {len(existing_data)} frames")
            
            for _, row in existing_data.iterrows():
                frame_id = self.create_frame(measurement_id, row['frame'])
                self.save_detection_data(frame_id, row['centers'], row['radii'], row['statistic'])
            
        except FileNotFoundError:
            print("No existing pickle data found, you'll need to run detection first")
        
        # Migrate vector field files
        vector_field_path = measure.get_vector_field_path()
        if vector_field_path.exists():
            print(f"Scanning vector field files in {vector_field_path}")
            vector_files = list(vector_field_path.glob("*.txt"))
            for file_path in tqdm(vector_files, desc="Migrating vector fields", unit="file", colour="blue"):
                # Parse filename to extract measurement, frames, and source
                # Format: measurement_name_DSC_xxxx_DSC_yyyy_source.txt
                parts = file_path.stem.split('_')
                if len(parts) == 6:

                    frame1_name = f"{parts[1]}_{parts[2]}.jpg"  # DSC_xxxx.jpg
                    frame2_name = f"{parts[3]}_{parts[4]}.jpg"  # DSC_yyyy.jpg
                    source = parts[5]  # Kdt / Piv

                    # print(f"Parsing {file_path.name}: {frame1_name} -> {frame2_name}, source: {source}")
                    
                    try:
                        frame1_id = self.get_frame_id(measure.get_name(), frame1_name)
                        frame2_id = self.get_frame_id(measure.get_name(), frame2_name)
                        
                        # Load the file data
                        data = pd.read_csv(file_path, sep="\t")
                        if source == "Piv": 
                            data.rename(columns={"# x": "x"}, inplace=True)
                        
                        vector_data = {col: data[col].to_numpy() for col in data.columns}
                        self.save_vector_field(measurement_id, frame1_id, frame2_id, source, vector_data)
                        # print(f"✓ Successfully migrated {file_path.name}")
                        
                    except ValueError as e:
                        print(f"✗ Skipping {file_path.name}: {e}")
                    except Exception as e:
                        print(f"✗ Failed to migrate {file_path}: {e}")
                else:
                    print(f"Skipping file with unexpected format: {file_path.name}")
        
        print(f"Migration completed for {measure.get_name()}")

    def _show_frames_in_db(self, measurement_name: str):
        """Debug helper to show what frames are in the database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT f.frame_name FROM measurements m
                JOIN frames f ON m.id = f.measurement_id
                WHERE m.name = ?
                ORDER BY f.frame_number
            """, (measurement_name,))
            
            frames = [row[0] for row in cursor.fetchall()]
            print(f"Frames in database ({len(frames)}): {', '.join(frames[:10])}{'...' if len(frames) > 10 else ''}")