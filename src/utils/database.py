import sqlite3
import json
import os
import datetime
from utils import resource_path

# Default database path inside the application data directory
def get_db_path():
    data_dir = resource_path('data')
    try:
        os.makedirs(data_dir, exist_ok=True)
    except Exception:
        pass
    return os.path.join(data_dir, 'dnax_sequences.db')

class SequenceDatabase:
    """Local SQLite Database Manager for storing and managing generated DNA sequences."""

    def __init__(self, db_path=None):
        self.db_path = db_path or get_db_path()
        self._init_db()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Creates the sequences table and indexes if they do not exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sequences (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    mode TEXT NOT NULL,
                    length INTEGER NOT NULL,
                    total_length INTEGER NOT NULL,
                    gc_pct REAL NOT NULL,
                    payload TEXT NOT NULL,
                    linear_seq TEXT NOT NULL,
                    primers_json TEXT,
                    probes_json TEXT,
                    notes TEXT
                )
            ''')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_sequences_name ON sequences(name)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_sequences_created ON sequences(created_at)')
            conn.commit()

    def save_sequence(self, name, payload, linear_seq, mode='linear', length=None,
                      total_length=None, gc_pct=None, primers=None, probes=None, notes=''):
        """
        Saves or updates a DNA sequence record.
        Returns the inserted/updated sequence ID.
        """
        name = name.strip()
        if not name:
            name = f"DNA_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"

        if length is None:
            length = len(payload)
        if total_length is None:
            total_length = len(linear_seq)
        if gc_pct is None:
            g = payload.count('G') + payload.count('g')
            c = payload.count('C') + payload.count('c')
            gc_pct = round(((g + c) / max(1, len(payload))) * 100, 2)

        primers_str = json.dumps(primers) if primers is not None else None
        probes_str = json.dumps(probes) if probes is not None else None

        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Insert or replace by name
            cursor.execute('''
                INSERT INTO sequences (
                    name, created_at, mode, length, total_length, gc_pct,
                    payload, linear_seq, primers_json, probes_json, notes
                ) VALUES (?, CURRENT_TIMESTAMP, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(name) DO UPDATE SET
                    created_at = CURRENT_TIMESTAMP,
                    mode = excluded.mode,
                    length = excluded.length,
                    total_length = excluded.total_length,
                    gc_pct = excluded.gc_pct,
                    payload = excluded.payload,
                    linear_seq = excluded.linear_seq,
                    primers_json = excluded.primers_json,
                    probes_json = excluded.probes_json,
                    notes = excluded.notes
            ''', (name, mode, length, total_length, gc_pct, payload, linear_seq, primers_str, probes_str, notes))
            conn.commit()
            return cursor.lastrowid

    def get_all_sequences(self, order_by='created_at DESC'):
        """Returns all sequence records as a list of dicts."""
        allowed_orders = ['created_at DESC', 'created_at ASC', 'name ASC', 'name DESC', 'length DESC', 'length ASC', 'id DESC']
        if order_by not in allowed_orders:
            order_by = 'created_at DESC'

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f'SELECT * FROM sequences ORDER BY {order_by}')
            rows = cursor.fetchall()
            results = []
            for row in rows:
                r_dict = dict(row)
                if r_dict.get('primers_json'):
                    try:
                        r_dict['primers'] = json.loads(r_dict['primers_json'])
                    except Exception:
                        r_dict['primers'] = None
                else:
                    r_dict['primers'] = None

                if r_dict.get('probes_json'):
                    try:
                        r_dict['probes'] = json.loads(r_dict['probes_json'])
                    except Exception:
                        r_dict['probes'] = None
                else:
                    r_dict['probes'] = None
                results.append(r_dict)
            return results

    def get_sequence_by_id(self, seq_id):
        """Retrieves a single sequence by primary key ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM sequences WHERE id = ?', (seq_id,))
            row = cursor.fetchone()
            if not row:
                return None
            r_dict = dict(row)
            if r_dict.get('primers_json'):
                try:
                    r_dict['primers'] = json.loads(r_dict['primers_json'])
                except Exception:
                    r_dict['primers'] = None
            if r_dict.get('probes_json'):
                try:
                    r_dict['probes'] = json.loads(r_dict['probes_json'])
                except Exception:
                    r_dict['probes'] = None
            return r_dict

    def get_sequence_by_name(self, name):
        """Retrieves a single sequence by unique name."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM sequences WHERE name = ?', (name,))
            row = cursor.fetchone()
            if not row:
                return None
            r_dict = dict(row)
            if r_dict.get('primers_json'):
                try:
                    r_dict['primers'] = json.loads(r_dict['primers_json'])
                except Exception:
                    r_dict['primers'] = None
            if r_dict.get('probes_json'):
                try:
                    r_dict['probes'] = json.loads(r_dict['probes_json'])
                except Exception:
                    r_dict['probes'] = None
            return r_dict

    def delete_sequence(self, seq_id):
        """Deletes a sequence by ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM sequences WHERE id = ?', (seq_id,))
            conn.commit()
            return cursor.rowcount > 0

    def count_sequences(self):
        """Returns the total number of stored sequences."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM sequences')
            return cursor.fetchone()[0]

    def search_sequences(self, query):
        """Searches sequences by name, notes, or partial payload sequence."""
        q = f"%{query.strip()}%"
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM sequences 
                WHERE name LIKE ? OR notes LIKE ? OR payload LIKE ?
                ORDER BY created_at DESC
            ''', (q, q, q))
            rows = cursor.fetchall()
            results = []
            for row in rows:
                r_dict = dict(row)
                if r_dict.get('primers_json'):
                    try:
                        r_dict['primers'] = json.loads(r_dict['primers_json'])
                    except Exception:
                        r_dict['primers'] = None
                if r_dict.get('probes_json'):
                    try:
                        r_dict['probes'] = json.loads(r_dict['probes_json'])
                    except Exception:
                        r_dict['probes'] = None
                results.append(r_dict)
            return results

# Singleton database instance
_db_instance = None

def get_db():
    global _db_instance
    if _db_instance is None:
        _db_instance = SequenceDatabase()
    return _db_instance
