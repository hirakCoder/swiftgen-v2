"""
SwiftGen V2 - Dynamic Timeout Management
Prevents timeout failures with intelligent timeout scaling
"""

from typing import Dict, Any
import time

class DynamicTimeoutManager:
    """Manages timeouts based on operation complexity"""
    
    def __init__(self):
        self.base_timeouts = {
            "simple_generation": 30,
            "complex_generation": 60,
            "hybrid_generation": 90,  # Increased for 3 LLM calls
            "build": 45,
            "simulator_install": 60,  # Increased for first-time install
            "simulator_launch": 30,
            "modification": 45
        }
        
        self.operation_history = {}
    
    def get_timeout(self, operation: str, complexity: float = 1.0) -> int:
        """Get appropriate timeout for operation"""
        base = self.base_timeouts.get(operation, 30)
        
        # Scale by complexity (1.0 = normal, 2.0 = double complexity)
        scaled = int(base * complexity)
        
        # Learn from history - if operation previously timed out, increase
        if operation in self.operation_history:
            last_duration = self.operation_history[operation]
            if last_duration > scaled * 0.9:  # Close to timeout
                scaled = int(scaled * 1.5)  # Increase by 50%
        
        return min(scaled, 300)  # Cap at 5 minutes
    
    def record_operation(self, operation: str, duration: float):
        """Record operation duration for learning"""
        self.operation_history[operation] = duration
    
    def get_circuit_breaker_config(self) -> Dict[str, Any]:
        """Get circuit breaker configuration with proper timeouts"""
        return {
            "failure_threshold": 3,
            "recovery_timeout": 10,
            "expected_exception": TimeoutError,
            "fallback_result": None,
            "timeout": self.get_timeout("complex_generation", 1.5)
        }
