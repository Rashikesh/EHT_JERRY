# backend/core/audit_chain.py
import hashlib
import json
import time
import threading

class Block:
    def __init__(self, index, timestamp, data, previous_hash):
        self.index = index
        self.timestamp = timestamp
        self.data = data
        self.previous_hash = previous_hash
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        block_string = json.dumps({
            "index": self.index,
            "timestamp": self.timestamp,
            "data": self.data,
            "previous_hash": self.previous_hash
        }, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

class AuditChain:
    _instance = None
    _lock = threading.Lock()  # Thread-safety (from Singleton Pattern guide)

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:  # Double-checked locking
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        self.chain = [self.create_genesis_block()]
        print("🔗 Immutable Audit Chain (Singleton) initialized")

    def create_genesis_block(self):
        return Block(0, time.time(), "Genesis Block - System Initialized", "0")

    def get_last_block(self):
        return self.chain[-1]

    def add_block(self, data):
        last_block = self.get_last_block()
        new_block = Block(
            index=last_block.index + 1,
            timestamp=time.time(),
            data=data,
            previous_hash=last_block.hash
        )
        self.chain.append(new_block)
        return new_block

# Global singleton instance
audit_chain = AuditChain()