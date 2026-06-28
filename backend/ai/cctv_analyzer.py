# backend/ai/cctv_analyzer.py
import time
import cv2
import numpy as np
from ultralytics import YOLO
import threading

class CCTVAnalyzer:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        
        # Load YOLOv8 model for object detection
        print("🎥 Loading CCTV AI Model (YOLOv8)...")
        self.model = YOLO('yolov8n.pt')  # or use custom trained model
        
        # Safety classes to detect
        self.safety_classes = {
            'person': 0,
            'hard_hat': 1,  # Custom class
            'safety_vest': 2,  # Custom class
            'smoke': 3,  # Custom class
            'fire': 4,  # Custom class
        }
        
        print("✅ CCTV Analyzer ready")
    
    def analyze_frame(self, frame: np.ndarray) -> dict:
        """Analyze a single frame for safety violations"""
        results = self.model(frame)
        
        alerts = []
        ppe_violations = []
        
        for result in results:
            boxes = result.boxes
            for box in boxes:
                cls = int(box.cls[0])
                conf = float(box.conf[0])
                
                # Detect missing PPE
                if cls == self.safety_classes['person']:
                    # Check if person has hard hat and vest nearby
                    # (simplified - in production, use pose estimation)
                    ppe_violations.append({
                        'type': 'missing_ppe',
                        'confidence': conf,
                        'bbox': box.xyxy[0].tolist()
                    })
                
                # Detect smoke or fire
                if cls in [self.safety_classes['smoke'], self.safety_classes['fire']]:
                    alerts.append({
                        'type': 'fire_detected' if cls == 4 else 'smoke_detected',
                        'confidence': conf,
                        'severity': 'critical'
                    })
        
        return {
            'alerts': alerts,
            'ppe_violations': ppe_violations,
            'person_count': len([b for b in results[0].boxes if int(b.cls[0]) == 0]),
            'timestamp': time.time()
        }

cctv_analyzer = CCTVAnalyzer()