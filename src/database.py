"""
database.py
A simplified, self-contained database manager for the PoC.
It creates and manages a local SQLite database (`poc_hopper.db`).
"""
import sqlite3
import time
import os
import json

class Database:
    def __init__(self, db_name="poc_hopper.db"):
        self.db_path = os.path.join(os.path.dirname(__file__), '..', db_name)
        # Ensure a clean slate for every demo run
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        self._init_db()
        print(f"[DB] Initialized and cleaned database at: {self.db_path}")

    def _init_db(self):
        """Initializes the database and the proofs table."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE proofs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL,
                source TEXT,
                source_tx TEXT UNIQUE,
                proof_a TEXT,
                proof_b TEXT,
                proof_c TEXT,
                pubs TEXT,
                status TEXT DEFAULT 'pending',
                zkv_extrinsic TEXT,
                error TEXT
            )
        ''')
        conn.commit()
        conn.close()

    def add_proof(self, source, source_tx, proof_a, proof_b, proof_c, pubs):
        """Adds a new proof to the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO proofs (timestamp, source, source_tx, proof_a, proof_b, proof_c, pubs, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'pending')
            ''', (time.time(), source, source_tx, proof_a, proof_b, proof_c, json.dumps(pubs)))
            conn.commit()
            print(f"[DB] Added proof from '{source}' with tx '{source_tx}'.")
            return True
        except sqlite3.IntegrityError:
            print(f"[DB] Warning: Proof with tx '{source_tx}' already exists.")
            return False
        finally:
            conn.close()

    def get_pending_proofs(self, limit=10):
        """Retrieves a list of pending proofs."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM proofs WHERE status = "pending" ORDER BY id ASC LIMIT ?', (limit,))
        rows = cursor.fetchall()
        conn.close()
        return rows

    def mark_status(self, proof_id, status, detail=""):
        """Marks a proof as 'verified' or 'failed'."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        if status == 'verified':
            cursor.execute('UPDATE proofs SET status = ?, zkv_extrinsic = ? WHERE id = ?', (status, detail, proof_id))
        else: # failed
            cursor.execute('UPDATE proofs SET status = ?, error = ? WHERE id = ?', (status, detail, proof_id))
        conn.commit()
        conn.close()
