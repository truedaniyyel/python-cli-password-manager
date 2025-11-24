import sys
import sqlite3
from pathlib import Path

def get_base_dir():
    if getattr(sys, 'frozen', False):
        # If run as an .exe, use the location of the .exe file
        return Path(sys.executable).parent
    else:
        # If run as a script, use the location of the script
        return Path(__file__).resolve().parent.parent

BASE_DIR = get_base_dir()
DATA_DIR = BASE_DIR / "data"
DB_FILE = DATA_DIR / "vault.db"

class StorageManager:
    def __init__(self):
        # Ensure the 'data' folder exists before connecting
        DATA_DIR.mkdir(parents=True, exist_ok=True)

        self.conn = sqlite3.connect(str(DB_FILE))
        self.cursor = self.conn.cursor()
        self._init_db()

    def _init_db(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS config (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        # Just one blob.
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS secrets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                encrypted_data BLOB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.conn.commit()

    def save_config(self, key, value):
        self.cursor.execute("INSERT OR REPLACE INTO config (key, value) VALUES (?, ?)", (key, value))
        self.conn.commit()

    def get_config(self, key):
        self.cursor.execute("SELECT value FROM config WHERE key=?", (key,))
        result = self.cursor.fetchone()
        return result[0] if result else None

    def add_secret(self, encrypted_blob):
        self.cursor.execute(
            "INSERT INTO secrets (encrypted_data) VALUES (?)",
            (encrypted_blob,)
        )
        self.conn.commit()

    def update_secret(self, secret_id, encrypted_blob):
        """Updates the blob for a specific ID."""
        self.cursor.execute(
            "UPDATE secrets SET encrypted_data = ? WHERE id = ?",
            (encrypted_blob, secret_id)
        )
        self.conn.commit()
        return self.cursor.rowcount > 0

    def get_all_blobs(self):
        """Returns the raw encrypted blobs. Decryption happens in main.py"""
        self.cursor.execute("SELECT id, encrypted_data FROM secrets")
        return self.cursor.fetchall()

    def delete_secret(self, secret_id):
        self.cursor.execute("DELETE FROM secrets WHERE id = ?", (secret_id,))
        count = self.cursor.rowcount
        self.conn.commit()
        return count > 0

    def close(self):
        self.conn.close()