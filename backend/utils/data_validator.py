class DataValidator:
    @staticmethod
    def validate_sensor_data(data: dict) -> tuple[bool, str]:
        """Returns (is_valid, error_message)"""
        
        # Gas should be 0-100%
        if not (0 <= data.get('gas', 0) <= 100):
            return False, f"Invalid gas reading: {data.get('gas')}%"
        
        # Pressure should be reasonable (1000-5000 bar)
        if not (1000 <= data.get('pressure', 0) <= 5000):
            return False, f"Invalid pressure: {data.get('pressure')} bar"
        
        # Temperature should be -50 to 200°C
        if not (-50 <= data.get('temperature', 0) <= 200):
            return False, f"Invalid temperature: {data.get('temperature')}°C"
        
        # Check for sudden spikes (>50% change in 2 seconds = likely noise)
        # You'd need to store previous values for this
        
        return True, "Valid"
