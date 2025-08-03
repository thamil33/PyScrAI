import json
import sqlite3
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, MutableMapping

from .simulation_state import SimulationState


def deep_update(
    source: MutableMapping, overrides: MutableMapping
) -> MutableMapping:
    """
    Update a nested dictionary or similar mapping.
    Modifies 'source' in place.
    """
    for key, value in overrides.items():
        if isinstance(value, MutableMapping) and isinstance(
            source.get(key), MutableMapping
        ):
            source[key] = deep_update(source.get(key, {}), value)
        else:
            source[key] = value
    return source


class StatePersistence(ABC):
    """Abstract base class for state persistence implementations."""
    
    @abstractmethod
    def save_state(self, state: SimulationState) -> None:
        """Save a simulation state."""
        pass
    
    @abstractmethod
    def load_state(self, simulation_id: str) -> Optional[SimulationState]:
        """Load a simulation state by ID."""
        pass
    
    @abstractmethod
    def update_state(self, simulation_id: str, updates: Dict[str, Any]) -> None:
        """Perform partial update to simulation state."""
        pass
    
    @abstractmethod
    def delete_simulation(self, simulation_id: str) -> None:
        """Delete a simulation and all its data."""
        pass
    
    @abstractmethod
    def list_simulations(self) -> List[Dict[str, Any]]:
        """List all simulations with metadata."""
        pass
    
    @abstractmethod
    def create_snapshot(self, simulation_id: str, name: str) -> str:
        """Create a snapshot of the current state."""
        pass
    
    @abstractmethod
    def restore_snapshot(self, snapshot_id: str) -> SimulationState:
        """Restore state from a snapshot."""
        pass
    
    @abstractmethod
    def get_state_history(self, simulation_id: str) -> List[SimulationState]:
        """Get version history for a simulation."""
        pass


class SQLitePersistence(StatePersistence):
    """SQLite-based persistence implementation with JSON schema support."""
    
    def __init__(self, db_path: Path = Path("./simulations/states.db")):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
    
    def _init_database(self):
        """Initialize the SQLite database with required tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Enable JSON1 extension if available
        try:
            cursor.execute("SELECT json('{}')") 
        except sqlite3.OperationalError:
            # JSON1 extension not available, will use text storage
            pass
        
        # Main simulation states table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS simulation_states (
                simulation_id TEXT PRIMARY KEY,
                state_data TEXT NOT NULL,  -- JSON serialized state
                version INTEGER NOT NULL DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # State history table for versioning
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS state_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                simulation_id TEXT NOT NULL,
                state_data TEXT NOT NULL,  -- JSON serialized state
                version INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (simulation_id) REFERENCES simulation_states (simulation_id)
            )
        """)
        
        # Snapshots table for checkpoints
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS snapshots (
                id TEXT PRIMARY KEY,
                simulation_id TEXT NOT NULL,
                name TEXT NOT NULL,
                state_data TEXT NOT NULL,  -- JSON serialized state
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (simulation_id) REFERENCES simulation_states (simulation_id)
            )
        """)
        
        # Create indexes for better performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_history_sim_id ON state_history(simulation_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_snapshots_sim_id ON snapshots(simulation_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_states_updated ON simulation_states(updated_at)")
        
        conn.commit()
        conn.close()
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get a database connection with proper configuration."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable dict-like access
        return conn
    
    def _serialize_state(self, state: SimulationState) -> str:
        """Serialize state to JSON string with proper handling of complex types."""
        return state.model_dump_json(exclude_none=False)
    
    def _deserialize_state(self, json_data: str) -> SimulationState:
        """Deserialize JSON string back to SimulationState."""
        data = json.loads(json_data)
        return SimulationState.model_validate(data)
    
    def save_state(self, state: SimulationState) -> None:
        """Save a simulation state with automatic versioning."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # Check if simulation exists
            cursor.execute(
                "SELECT version FROM simulation_states WHERE simulation_id = ?",
                (state.simulation_id,)
            )
            result = cursor.fetchone()
            
            if result:
                # Update existing simulation
                current_version = result['version']
                state.version = current_version + 1
                
                # Archive current state to history
                cursor.execute(
                    "SELECT state_data FROM simulation_states WHERE simulation_id = ?",
                    (state.simulation_id,)
                )
                current_data = cursor.fetchone()
                if current_data:
                    cursor.execute(
                        """INSERT INTO state_history (simulation_id, state_data, version)
                           VALUES (?, ?, ?)""",
                        (state.simulation_id, current_data['state_data'], current_version)
                    )
                
                # Update current state
                cursor.execute(
                    """UPDATE simulation_states 
                       SET state_data = ?, version = ?, updated_at = CURRENT_TIMESTAMP
                       WHERE simulation_id = ?""",
                    (self._serialize_state(state), state.version, state.simulation_id)
                )
            else:
                # Insert new simulation
                state.version = 1
                cursor.execute(
                    """INSERT INTO simulation_states (simulation_id, state_data, version)
                       VALUES (?, ?, ?)""",
                    (state.simulation_id, self._serialize_state(state), state.version)
                )
            
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise RuntimeError(f"Failed to save state: {e}") from e
        finally:
            conn.close()
    
    def load_state(self, simulation_id: str) -> Optional[SimulationState]:
        """Load a simulation state by ID."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "SELECT state_data FROM simulation_states WHERE simulation_id = ?",
                (simulation_id,)
            )
            result = cursor.fetchone()
            
            if result:
                return self._deserialize_state(result['state_data'])
            return None
        finally:
            conn.close()
    
    def update_state(self, simulation_id: str, updates: Dict[str, Any]) -> None:
        """Perform partial update to simulation state."""
        # Load current state
        current_state = self.load_state(simulation_id)
        if not current_state:
            raise ValueError(f"Simulation {simulation_id} not found")
        
        # Apply updates using deep_update
        state_dict = current_state.model_dump()
        updated_dict = deep_update(state_dict, updates)
        
        # Update timestamp
        updated_dict['timestamp'] = datetime.now()
        
        # Create updated state and save
        updated_state = SimulationState.model_validate(updated_dict)
        self.save_state(updated_state)
    
    def delete_simulation(self, simulation_id: str) -> None:
        """Delete a simulation and all its data."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # Delete in order to respect foreign key constraints
            cursor.execute("DELETE FROM snapshots WHERE simulation_id = ?", (simulation_id,))
            cursor.execute("DELETE FROM state_history WHERE simulation_id = ?", (simulation_id,))
            cursor.execute("DELETE FROM simulation_states WHERE simulation_id = ?", (simulation_id,))
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise RuntimeError(f"Failed to delete simulation: {e}") from e
        finally:
            conn.close()
    
    def list_simulations(self) -> List[Dict[str, Any]]:
        """List all simulations with metadata."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT simulation_id, version, created_at, updated_at,
                       json_extract(state_data, '$.metadata') as metadata
                FROM simulation_states
                ORDER BY updated_at DESC
            """)
            
            results = []
            for row in cursor.fetchall():
                sim_info = {
                    'simulation_id': row['simulation_id'],
                    'version': row['version'],
                    'created_at': row['created_at'],
                    'updated_at': row['updated_at'],
                    'metadata': json.loads(row['metadata']) if row['metadata'] else {}
                }
                results.append(sim_info)
            
            return results
        finally:
            conn.close()
    
    def create_snapshot(self, simulation_id: str, name: str) -> str:
        """Create a snapshot of the current state."""
        # Load current state
        current_state = self.load_state(simulation_id)
        if not current_state:
            raise ValueError(f"Simulation {simulation_id} not found")
        
        snapshot_id = str(uuid.uuid4())
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                """INSERT INTO snapshots (id, simulation_id, name, state_data)
                   VALUES (?, ?, ?, ?)""",
                (snapshot_id, simulation_id, name, self._serialize_state(current_state))
            )
            conn.commit()
            return snapshot_id
        except Exception as e:
            conn.rollback()
            raise RuntimeError(f"Failed to create snapshot: {e}") from e
        finally:
            conn.close()
    
    def restore_snapshot(self, snapshot_id: str) -> SimulationState:
        """Restore state from a snapshot."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                "SELECT state_data FROM snapshots WHERE id = ?",
                (snapshot_id,)
            )
            result = cursor.fetchone()
            
            if not result:
                raise ValueError(f"Snapshot {snapshot_id} not found")
            
            return self._deserialize_state(result['state_data'])
        finally:
            conn.close()
    
    def get_state_history(self, simulation_id: str) -> List[SimulationState]:
        """Get version history for a simulation."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute(
                """SELECT state_data FROM state_history 
                   WHERE simulation_id = ? 
                   ORDER BY version ASC""",
                (simulation_id,)
            )
            
            history = []
            for row in cursor.fetchall():
                history.append(self._deserialize_state(row['state_data']))
            
            # Also include current state
            current_state = self.load_state(simulation_id)
            if current_state:
                history.append(current_state)
            
            return history
        finally:
            conn.close()


class JSONPersistence(StatePersistence):
    """JSON file-based persistence implementation."""
    
    def __init__(self, storage_dir: Path = Path("./simulations")):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        self.history_dir = self.storage_dir / "history"
        self.history_dir.mkdir(exist_ok=True)
        self.snapshots_dir = self.storage_dir / "snapshots"
        self.snapshots_dir.mkdir(exist_ok=True)
    
    def _get_state_file(self, simulation_id: str) -> Path:
        """Get the file path for a simulation state."""
        return self.storage_dir / f"{simulation_id}.json"
    
    def _get_history_file(self, simulation_id: str, version: int) -> Path:
        """Get the file path for a specific version."""
        return self.history_dir / f"{simulation_id}_v{version}.json"
    
    def save_state(self, state: SimulationState) -> None:
        """Save a simulation state to JSON file."""
        state_file = self._get_state_file(state.simulation_id)
        
        # If state exists, archive current version
        if state_file.exists():
            current_state = self.load_state(state.simulation_id)
            if current_state:
                history_file = self._get_history_file(state.simulation_id, current_state.version)
                with open(history_file, 'w') as f:
                    f.write(current_state.model_dump_json(indent=2))
                state.version = current_state.version + 1
            else:
                state.version = 1
        else:
            state.version = 1
        
        # Update timestamp
        state.timestamp = datetime.now()
        
        # Save current state
        with open(state_file, 'w') as f:
            f.write(state.model_dump_json(indent=2))
    
    def load_state(self, simulation_id: str) -> Optional[SimulationState]:
        """Load a simulation state from JSON file."""
        state_file = self._get_state_file(simulation_id)
        
        if not state_file.exists():
            return None
        
        try:
            with open(state_file, 'r') as f:
                data = json.load(f)
            return SimulationState.model_validate(data)
        except Exception as e:
            raise RuntimeError(f"Failed to load state {simulation_id}: {e}") from e
    
    def update_state(self, simulation_id: str, updates: Dict[str, Any]) -> None:
        """Perform partial update to simulation state."""
        current_state = self.load_state(simulation_id)
        if not current_state:
            raise ValueError(f"Simulation {simulation_id} not found")
        
        # Apply updates using deep_update
        state_dict = current_state.model_dump()
        updated_dict = deep_update(state_dict, updates)
        
        # Create updated state and save
        updated_state = SimulationState.model_validate(updated_dict)
        self.save_state(updated_state)
    
    def delete_simulation(self, simulation_id: str) -> None:
        """Delete a simulation and all its data."""
        # Delete main state file
        state_file = self._get_state_file(simulation_id)
        if state_file.exists():
            state_file.unlink()
        
        # Delete history files
        for history_file in self.history_dir.glob(f"{simulation_id}_v*.json"):
            history_file.unlink()
        
        # Delete snapshots
        for snapshot_file in self.snapshots_dir.glob(f"{simulation_id}_*.json"):
            snapshot_file.unlink()
    
    def list_simulations(self) -> List[Dict[str, Any]]:
        """List all simulations with metadata."""
        simulations = []
        
        for state_file in self.storage_dir.glob("*.json"):
            try:
                state = self.load_state(state_file.stem)
                if state:
                    simulations.append({
                        'simulation_id': state.simulation_id,
                        'version': state.version,
                        'created_at': state.timestamp.isoformat(),
                        'updated_at': state.timestamp.isoformat(),
                        'metadata': state.metadata
                    })
            except Exception:
                # Skip corrupted files
                continue
        
        return sorted(simulations, key=lambda x: x['updated_at'], reverse=True)
    
    def create_snapshot(self, simulation_id: str, name: str) -> str:
        """Create a snapshot of the current state."""
        current_state = self.load_state(simulation_id)
        if not current_state:
            raise ValueError(f"Simulation {simulation_id} not found")
        
        snapshot_id = str(uuid.uuid4())
        snapshot_file = self.snapshots_dir / f"{simulation_id}_{snapshot_id}.json"
        
        snapshot_data = {
            'id': snapshot_id,
            'name': name,
            'simulation_id': simulation_id,
            'created_at': datetime.now().isoformat(),
            'state': current_state.model_dump()
        }
        
        with open(snapshot_file, 'w') as f:
            json.dump(snapshot_data, f, indent=2)
        
        return snapshot_id
    
    def restore_snapshot(self, snapshot_id: str) -> SimulationState:
        """Restore state from a snapshot."""
        for snapshot_file in self.snapshots_dir.glob(f"*_{snapshot_id}.json"):
            try:
                with open(snapshot_file, 'r') as f:
                    snapshot_data = json.load(f)
                
                if snapshot_data['id'] == snapshot_id:
                    return SimulationState.model_validate(snapshot_data['state'])
            except Exception:
                continue
        
        raise ValueError(f"Snapshot {snapshot_id} not found")
    
    def get_state_history(self, simulation_id: str) -> List[SimulationState]:
        """Get version history for a simulation."""
        history = []
        
        # Load all history files
        history_files = list(self.history_dir.glob(f"{simulation_id}_v*.json"))
        history_files.sort(key=lambda f: int(f.stem.split('_v')[1]))
        
        for history_file in history_files:
            try:
                with open(history_file, 'r') as f:
                    data = json.load(f)
                history.append(SimulationState.model_validate(data))
            except Exception:
                continue
        
        # Add current state
        current_state = self.load_state(simulation_id)
        if current_state:
            history.append(current_state)
        
        return history