import sqlite3
import numpy as np
import json
import pickle
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import pandas as pd
from tqdm import tqdm
import time
from threading import Lock

class DatabaseManager:
    def __init__(self, db_path: str = "db/measurements.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Performance optimizations
        self._cache = {}  # Memory cache for frequently accessed data
        self._cache_lock = Lock()
        self._last_measurement = None
        self._preloaded_data = {}
        
        # Performance tracking
        self._access_stats = {}
        
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables and performance optimizations."""
        with sqlite3.connect(self.db_path) as conn:
            # Performance optimizations
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA cache_size=100000")  # 100MB cache
            conn.execute("PRAGMA temp_store=memory")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.execute("PRAGMA mmap_size=1073741824")  # 1GB memory map
            conn.execute("PRAGMA page_size=65536")  # Larger page size
            
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS measurements (
                    id INTEGER PRIMARY KEY,
                    name TEXT UNIQUE NOT NULL,
                    total_frames INTEGER DEFAULT 0,
                    date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS frames (
                    id INTEGER PRIMARY KEY,
                    measurement_id INTEGER,
                    frame_name TEXT NOT NULL,
                    frame_number INTEGER,
                    has_detection BOOLEAN DEFAULT 0,
                    detection_file_path TEXT,
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
                
                CREATE TABLE IF NOT EXISTS vector_field_index (
                    id INTEGER PRIMARY KEY,
                    measurement_id INTEGER,
                    frame1_id INTEGER,
                    frame2_id INTEGER,
                    source TEXT,
                    file_path TEXT NOT NULL,
                    file_size INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (measurement_id) REFERENCES measurements (id),
                    FOREIGN KEY (frame1_id) REFERENCES frames (id),
                    FOREIGN KEY (frame2_id) REFERENCES frames (id)
                );
                
                CREATE TABLE IF NOT EXISTS trajectories_cache (
                    id INTEGER PRIMARY KEY,
                    measurement_id INTEGER,
                    trajectory_data BLOB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (measurement_id) REFERENCES measurements (id)
                );
                
                -- Performance indexes
                CREATE INDEX IF NOT EXISTS idx_frames_measurement ON frames(measurement_id);
                CREATE INDEX IF NOT EXISTS idx_frames_lookup ON frames(measurement_id, frame_name);
                CREATE INDEX IF NOT EXISTS idx_detections_frame ON detections(frame_id);
                CREATE INDEX IF NOT EXISTS idx_vector_fields_lookup 
                    ON vector_fields(measurement_id, frame1_id, frame2_id, source);
                CREATE INDEX IF NOT EXISTS idx_vector_field_index_lookup 
                    ON vector_field_index(measurement_id, frame1_id, frame2_id, source);
                CREATE INDEX IF NOT EXISTS idx_trajectories_measurement ON trajectories_cache(measurement_id);
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
        measurement_id = self._get_measurement_id(measurement_name)
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT f.frame_name, d.centers, d.radii, d.statistics
                FROM detections d
                JOIN frames f ON d.frame_id = f.id
                WHERE f.measurement_id = ?
                ORDER BY f.frame_number
            """, (measurement_id,))
            
            rows = cursor.fetchall()
        
            if not rows:
                return pd.DataFrame()
        
            # Convert to the same format as pickle files
            data = []
            for frame_name, centers_blob, radii_blob, statistics_str in rows:
                centers = self._deserialize_array(centers_blob)
                radii = self._deserialize_array(radii_blob)
                statistics = json.loads(statistics_str) if statistics_str else {}
                
                data.append({
                    'frame': frame_name,
                    'centers': centers,
                    'radii': radii,
                    'statistic': statistics  # Note: singular 'statistic' to match pickle format
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
        """Migrate existing data from files to database with new optimized schema."""
        print(f"Migrating measurement {measure.get_name()} to database...")
        
        # Create measurement with new schema
        measurement_id = self.create_measurement(measure.get_name())
        
       
        # Load existing pickle file (detection data)
        try:
            existing_data = measure.load_pickled_data(source='drive')
            print(f"Found existing pickle data with {len(existing_data)} frames")
            
            # Update measurement with total frames count
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "UPDATE measurements SET total_frames = ? WHERE id = ?",
                    (len(existing_data), measurement_id)
                )
            
            # Migrate detection data
            for _, row in tqdm(existing_data.iterrows(), desc="Migrating detection data", 
                                total=len(existing_data), unit="frame", colour="green"):
                frame_id = self.create_frame(measurement_id, row['frame'])
                self.save_detection_data(frame_id, row['centers'], row['radii'], row['statistic'])
            
            print(f"✓ Migrated {len(existing_data)} detection frames")
            
        except FileNotFoundError:
            print("No existing pickle data found")
        
        # Migrate vector field files
        vector_field_path = measure.get_vector_field_path()
        if vector_field_path.exists():
            print(f"Scanning vector field files in {vector_field_path}")
            vector_files = list(vector_field_path.glob("*.txt"))
            
            if vector_files:
                print(f"Found {len(vector_files)} vector field files to migrate")
                
                migrated_count = 0
                skipped_count = 0
                
                for file_path in tqdm(vector_files, desc="Migrating vector fields", unit="file", colour="blue"):
                    try:
                        # Parse filename - handle different formats
                        if self._migrate_single_vector_field(file_path, measure.get_name(), measurement_id):
                            migrated_count += 1
                        else:
                            skipped_count += 1
                            
                    except Exception as e:
                        print(f"✗ Failed to migrate {file_path.name}: {e}")
                        skipped_count += 1
                
                print(f"✓ Migrated {migrated_count} vector field files")
                if skipped_count > 0:
                    print(f"⚠ Skipped {skipped_count} files (format issues or missing frames)")
            else:
                print("No vector field files found")
        
        # Now register files for fast access (populate the new index tables)
        print("Creating file index for fast access...")
        self._build_file_index(measure, measurement_id)
        
        print(f"✅ Migration completed for {measure.get_name()}")
            

    def _migrate_single_vector_field(self, file_path: Path, measurement_name: str, measurement_id: int) -> bool:
        """Migrate a single vector field file, handling different naming formats"""
        parts = file_path.stem.split('_')
        
        # Handle different file naming formats
        if len(parts) == 6:
            # Alternative format: measurement_DSC_xxxx_DSC_yyyy_source.txt
            frame1_name = f"{parts[1]}_{parts[2]}.jpg"  # DSC_xxxx.jpg
            frame2_name = f"{parts[3]}_{parts[4]}.jpg"  # DSC_yyyy.jpg
            source = parts[5]  # Kdt/Piv
        else:
            print(f"⚠ Unexpected filename format: {file_path.name}")
            return False
        
        try:
            # Get or create frame IDs
            frame1_id = self._get_or_create_frame_for_migration(measurement_id, frame1_name)
            frame2_id = self._get_or_create_frame_for_migration(measurement_id, frame2_name)
            
            # Load the file data
            data = pd.read_csv(file_path, sep="\t")
            if source == "Piv": 
                data.rename(columns={"# x": "x"}, inplace=True)
            
            vector_data = {col: data[col].to_numpy() for col in data.columns}
            
            # Save to database
            self.save_vector_field(measurement_id, frame1_id, frame2_id, source, vector_data)
            
            # Also add to file index for fast access
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """INSERT OR REPLACE INTO vector_field_index 
                       (measurement_id, frame1_id, frame2_id, source, file_path, file_size)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (measurement_id, frame1_id, frame2_id, source, 
                     str(file_path), file_path.stat().st_size)
                )
            
            return True
            
        except Exception as e:
            # For debugging specific files
            # print(f"Failed to migrate {file_path.name}: {e}")
            return False

    def _get_or_create_frame_for_migration(self, measurement_id: int, frame_name: str) -> int:
        """Get or create frame ID during migration"""
        try:
            # Try to get existing frame
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT id FROM frames WHERE measurement_id = ? AND frame_name = ?",
                    (measurement_id, frame_name)
                )
                result = cursor.fetchone()
                
                if result:
                    return result[0]
                else:
                    # Create new frame (this might be a frame that wasn't in detection data)
                    return self._create_frame_without_detection(measurement_id, frame_name)
                    
        except Exception as e:
            print(f"⚠ Error getting/creating frame: {e}")
            # # Create new frame
            # return self._create_frame_without_detection(measurement_id, frame_name)

    def _create_frame_without_detection(self, measurement_id: int, frame_name: str) -> int:
        """Create a frame record without detection data (for vector field only frames)"""
        try:
            frame_number = int(frame_name.split('_')[1].split('.')[0])
        except (IndexError, ValueError):
            frame_number = 0  # Fallback
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "INSERT OR IGNORE INTO frames (measurement_id, frame_name, frame_number, has_detection) VALUES (?, ?, ?, ?)",
                (measurement_id, frame_name, frame_number, False)
            )
            if cursor.rowcount == 0:
                cursor = conn.execute(
                    "SELECT id FROM frames WHERE measurement_id = ? AND frame_name = ?",
                    (measurement_id, frame_name)
                )
                return cursor.fetchone()[0]
            return cursor.lastrowid

    def _build_file_index(self, measure, measurement_id: int):
        """Build file index for fast access"""
        try:
            # Index detection file
            detection_file = measure.path / f"data_drive_{measure.get_name()}.pkl"
            if detection_file.exists():
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute(
                        """UPDATE frames SET detection_file_path = ? 
                           WHERE measurement_id = ? AND has_detection = 1""",
                        (str(detection_file), measurement_id)
                    )
            
            print("✓ File index created")
            
        except Exception as e:
            print(f"⚠ Could not build complete file index: {e}")

    # Performance optimization methods
    def preload_measurement(self, measurement_name: str):
        """Preload frequently accessed data for a measurement"""
        if self._last_measurement == measurement_name:
            return  # Already loaded
        
        print(f"🚀 Preloading {measurement_name} for optimal GUI performance...")
        start_time = time.time()
        
        with self._cache_lock:
            # Clear old cache
            self._cache.clear()
            self._preloaded_data.clear()
            
            # Load detection data into memory (for particle tracking)
            try:
                detection_data = self.load_detection_data(measurement_name)
                self._preloaded_data['detection'] = detection_data
                print(f"  ✓ Loaded {len(detection_data)} detection frames")
            except Exception as e:
                print(f"  ✗ Could not load detection data: {e}")
            
            # Cache vector field file paths for fast access
            try:
                vector_field_paths = self._index_vector_field_files(measurement_name)
                self._preloaded_data['vector_field_paths'] = vector_field_paths
                print(f"  ✓ Indexed {len(vector_field_paths)} vector field files")
            except Exception as e:
                print(f"  ✗ Could not index vector field files: {e}")
            
            self._last_measurement = measurement_name
            
        load_time = time.time() - start_time
        print(f"  🎯 Preload completed in {load_time:.2f}s")

    def _index_vector_field_files(self, measurement_name: str) -> Dict[str, Path]:
        """Index vector field files for fast access"""
        vector_field_paths = {}
        measurement_id = self._get_measurement_id(measurement_name)
        
        # First, try to get from database index
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT f1.frame_name, f2.frame_name, vfi.source, vfi.file_path
                FROM vector_field_index vfi
                JOIN frames f1 ON vfi.frame1_id = f1.id
                JOIN frames f2 ON vfi.frame2_id = f2.id
                WHERE vfi.measurement_id = ?
            """, (measurement_id,))
            
            for frame1, frame2, source, file_path in cursor.fetchall():
                key = f"{frame1}_{frame2}_{source}"
                if Path(file_path).exists():
                    vector_field_paths[key] = Path(file_path)
        
        # If no indexed files, fall back to file system scan
        if not vector_field_paths:
            from measurements_detectors import Measure
            measure = Measure(measurement_name, path_setting='drive', use_database=False)
            vector_field_path = measure.get_vector_field_path()
            
            if vector_field_path.exists():
                for file_path in vector_field_path.glob("*.txt"):
                    parts = file_path.stem.split('_')
                    if len(parts) >= 8:
                        frame1_name = f"{parts[3]}_{parts[4]}.jpg"
                        frame2_name = f"{parts[5]}_{parts[6]}.jpg"
                        source = parts[7]
                        key = f"{frame1_name}_{frame2_name}_{source}"
                        vector_field_paths[key] = file_path
        
        return vector_field_paths

    def load_vector_field_fast(self, measurement_name: str, frame1_name: str, 
                              frame2_name: str, source: str) -> Dict[str, np.ndarray]:
        """Load vector field data with optimized caching"""
        self.preload_measurement(measurement_name)
        
        cache_key = f"{measurement_name}_{frame1_name}_{frame2_name}_{source}"
        
        # Check memory cache first
        with self._cache_lock:
            if cache_key in self._cache:
                self._track_access(cache_key, 'cache_hit')
                return self._cache[cache_key]
        
        # Load from file using preloaded paths
        file_path_key = f"{frame1_name}_{frame2_name}_{source}"
        vector_field_paths = self._preloaded_data.get('vector_field_paths', {})
        
        if file_path_key not in vector_field_paths:
            # Fall back to database method
            try:
                return self.load_vector_field(measurement_name, frame1_name, frame2_name, source)
            except:
                raise FileNotFoundError(f"Vector field not found: {file_path_key}")
        
        file_path = vector_field_paths[file_path_key]
        
        start_time = time.time()
        
        # Fast file loading
        data = pd.read_csv(file_path, sep="\t")
        if source == "Piv":
            data.rename(columns={"# x": "x"}, inplace=True)
        
        result = {col: data[col].to_numpy() for col in data.columns}
        
        # Cache the result (limit cache size)
        with self._cache_lock:
            if len(self._cache) > 50:  # Limit cache size
                # Remove oldest entries
                oldest_key = next(iter(self._cache))
                del self._cache[oldest_key]
            
            self._cache[cache_key] = result
        
        load_time = time.time() - start_time
        self._track_access(cache_key, 'file_load', load_time)
        
        return result

    def get_detection_data_fast(self, measurement_name: str) -> pd.DataFrame:
        """Get detection data (optimized for ParticleTracker)"""
        self.preload_measurement(measurement_name)
        return self._preloaded_data.get('detection', pd.DataFrame())

    def cache_trajectories(self, measurement_name: str, trajectories: List):
        """Cache trajectories for ParticleTracker"""
        measurement_id = self._get_measurement_id(measurement_name)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO trajectories_cache (measurement_id, trajectory_data) VALUES (?, ?)",
                (measurement_id, pickle.dumps(trajectories))
            )

    def load_trajectories(self, measurement_name: str) -> Optional[List]:
        """Load cached trajectories"""
        try:
            measurement_id = self._get_measurement_id(measurement_name)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT trajectory_data FROM trajectories_cache WHERE measurement_id = ?",
                    (measurement_id,)
                )
                result = cursor.fetchone()
                
                if result:
                    return pickle.loads(result[0])
        except:
            pass
        return None

    def register_measurement_files(self, measure) -> int:
        """Register a measurement and index its files for fast access"""
        print(f"📋 Registering measurement {measure.get_name()}...")
        
        with sqlite3.connect(self.db_path) as conn:
            # Update measurement record with total frames
            try:
                total_frames = measure.get_total_frames_num()
            except:
                total_frames = 0
                
            cursor = conn.execute(
                "INSERT OR REPLACE INTO measurements (name, total_frames) VALUES (?, ?)",
                (measure.get_name(), total_frames)
            )
            measurement_id = cursor.lastrowid or conn.execute(
                "SELECT id FROM measurements WHERE name = ?", (measure.get_name(),)
            ).fetchone()[0]
            
            # Index detection files (if they exist)
            try:
                detection_data = measure.load_pickled_data(source='drive')
                detection_file = measure.path / f"data_drive_{measure.get_name()}.pkl"
                
                for _, row in detection_data.iterrows():
                    frame_id = self._create_frame_if_not_exists(conn, measurement_id, row['frame'])
                    conn.execute(
                        "UPDATE frames SET has_detection = 1, detection_file_path = ? WHERE id = ?",
                        (str(detection_file), frame_id)
                    )
                print(f"  ✓ Indexed {len(detection_data)} detection frames")
            except FileNotFoundError:
                print("  ℹ No detection data found")
            
            # Index vector field files
            vector_field_path = measure.get_vector_field_path()
            if vector_field_path.exists():
                indexed_count = 0
                for file_path in vector_field_path.glob("*.txt"):
                    if self._index_single_vector_field_file(conn, measurement_id, file_path):
                        indexed_count += 1
                print(f"  ✓ Indexed {indexed_count} vector field files")
            
            return measurement_id

    def _create_frame_if_not_exists(self, conn, measurement_id: int, frame_name: str) -> int:
        """Helper to create frame record if it doesn't exist"""
        frame_number = int(frame_name.split('_')[1].split('.')[0])
        cursor = conn.execute(
            "INSERT OR IGNORE INTO frames (measurement_id, frame_name, frame_number) VALUES (?, ?, ?)",
            (measurement_id, frame_name, frame_number)
        )
        if cursor.rowcount == 0:
            cursor = conn.execute(
                "SELECT id FROM frames WHERE measurement_id = ? AND frame_name = ?",
                (measurement_id, frame_name)
            )
            return cursor.fetchone()[0]
        return cursor.lastrowid

    def _index_single_vector_field_file(self, conn, measurement_id: int, file_path: Path) -> bool:
        """Index a single vector field file"""
        try:
            parts = file_path.stem.split('_')
            if len(parts) >= 8:
                frame1_name = f"{parts[3]}_{parts[4]}.jpg"
                frame2_name = f"{parts[5]}_{parts[6]}.jpg"
                source = parts[7]
                
                frame1_id = self._create_frame_if_not_exists(conn, measurement_id, frame1_name)
                frame2_id = self._create_frame_if_not_exists(conn, measurement_id, frame2_name)
                
                conn.execute(
                    """INSERT OR REPLACE INTO vector_field_index 
                       (measurement_id, frame1_id, frame2_id, source, file_path, file_size)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (measurement_id, frame1_id, frame2_id, source, 
                     str(file_path), file_path.stat().st_size)
                )
                return True
        except Exception:
            pass
        return False

    def _get_measurement_id(self, measurement_name: str) -> int:
        """Get measurement ID"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT id FROM measurements WHERE name = ?", (measurement_name,))
            result = cursor.fetchone()
            if not result:
                raise ValueError(f"Measurement {measurement_name} not found")
            return result[0]

    def _track_access(self, key: str, access_type: str, duration: float = 0):
        """Track access patterns for optimization"""
        if key not in self._access_stats:
            self._access_stats[key] = {'hits': 0, 'total_time': 0, 'avg_time': 0}
        
        self._access_stats[key]['hits'] += 1
        if duration > 0:
            self._access_stats[key]['total_time'] += duration
            self._access_stats[key]['avg_time'] = (
                self._access_stats[key]['total_time'] / self._access_stats[key]['hits']
            )

    def get_performance_stats(self) -> Dict:
        """Get performance statistics"""
        return {
            'cache_size': len(self._cache),
            'preloaded_measurement': self._last_measurement,
            'access_stats': dict(sorted(
                self._access_stats.items(), 
                key=lambda x: x[1]['hits'], 
                reverse=True
            )[:10])  # Top 10 most accessed
        }

    def get_available_vector_fields(self, measurement_name: str) -> List[tuple]:
        """Get available vector field combinations (for GUI dropdowns)"""
        measurement_id = self._get_measurement_id(measurement_name)
        
        with sqlite3.connect(self.db_path) as conn:
            # Try indexed files first
            cursor = conn.execute("""
                SELECT f1.frame_name, f2.frame_name, vfi.source, f1.frame_number, f2.frame_number
                FROM vector_field_index vfi
                JOIN frames f1 ON vfi.frame1_id = f1.id
                JOIN frames f2 ON vfi.frame2_id = f2.id
                WHERE vfi.measurement_id = ?
                ORDER BY f1.frame_number, f2.frame_number
            """, (measurement_id,))
            
            results = cursor.fetchall()
            
            # If no indexed files, fall back to database vector fields
            if not results:
                cursor = conn.execute("""
                    SELECT f1.frame_name, f2.frame_name, vf.source, f1.frame_number, f2.frame_number
                    FROM vector_fields vf
                    JOIN frames f1 ON vf.frame1_id = f1.id
                    JOIN frames f2 ON vf.frame2_id = f2.id
                    WHERE vf.measurement_id = ?
                    ORDER BY f1.frame_number, f2.frame_number
                """, (measurement_id,))
                results = cursor.fetchall()
            
            return results

    def clear_cache(self):
        """Clear memory cache"""
        with self._cache_lock:
            self._cache.clear()
            self._preloaded_data.clear()
            self._last_measurement = None
        print("🧹 Cache cleared")