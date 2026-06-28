# backend/audit_logger.py
import sqlite3
import threading
from datetime import datetime

class AuditLogger:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized') and self._initialized:
            return
        self._initialized = True
        
        self.db_path = "audit.db"
        self._init_database()
    
    def _init_database(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS permit_log(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                gas REAL,
                pressure REAL,
                temp REAL,
                action TEXT,
                reason TEXT,
                ai_justification TEXT
            )
        """)
        conn.commit()
        conn.close()
    
    def log(self, gas: float, pressure: float, temp: float, 
            action: str, reason: str, ai_justification: str = ""):
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            INSERT INTO permit_log 
            (timestamp, gas, pressure, temp, action, reason, ai_justification)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().isoformat(),
            gas, pressure, temp,
            action, reason, ai_justification
        ))
        conn.commit()
        conn.close()
    
    def get_latest(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute(
            "SELECT * FROM permit_log ORDER BY id DESC LIMIT 1"
        )
        row = cursor.fetchone()
        conn.close()
        return row

# Global singleton
audit_logger = AuditLogger()