"""
Circuit Breaker Pattern - Prevents infinite loops and cascading failures
Used by Netflix, Amazon, and every production system that doesn't want to die
"""

import asyncio
import time
from typing import Any, Callable, Optional
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timedelta

class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject calls
    HALF_OPEN = "half_open"  # Testing if service recovered

@dataclass
class CircuitStats:
    """Track circuit breaker statistics"""
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    last_failure_time: Optional[datetime] = None
    consecutive_failures: int = 0
    
class CircuitBreakerError(Exception):
    """Raised when circuit is open"""
    pass

class CircuitBreaker:
    """
    Production-grade circuit breaker
    Prevents infinite retries and cascading failures
    """
    
    def __init__(
        self,
        name: str,
        failure_threshold: int = 3,
        timeout: float = 30.0,
        reset_timeout: float = 60.0,
        half_open_max_calls: int = 1
    ):
        """
        Args:
            name: Circuit breaker name for logging
            failure_threshold: Failures before opening circuit
            timeout: Max time for each call (seconds)
            reset_timeout: Time before trying again when open (seconds)
            half_open_max_calls: Test calls in half-open state
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.reset_timeout = reset_timeout
        self.half_open_max_calls = half_open_max_calls
        
        self.state = CircuitState.CLOSED
        self.stats = CircuitStats()
        self.last_state_change = datetime.now()
        self.half_open_calls = 0
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function through circuit breaker
        """
        # Check if we should attempt the call
        if not self._can_attempt():
            raise CircuitBreakerError(
                f"Circuit breaker '{self.name}' is OPEN. "
                f"Service unavailable after {self.stats.consecutive_failures} failures. "
                f"Will retry in {self._time_until_retry():.0f} seconds."
            )
        
        # Track call
        self.stats.total_calls += 1
        
        try:
            # Execute with timeout
            result = await asyncio.wait_for(
                func(*args, **kwargs),
                timeout=self.timeout
            )
            
            # Success - update state
            self._on_success()
            return result
            
        except asyncio.TimeoutError:
            self._on_failure()
            raise TimeoutError(
                f"Circuit breaker '{self.name}': Call timed out after {self.timeout}s"
            )
            
        except Exception as e:
            self._on_failure()
            raise
    
    def _can_attempt(self) -> bool:
        """Check if we should allow this call"""
        self._update_state()
        
        if self.state == CircuitState.CLOSED:
            return True
        
        if self.state == CircuitState.HALF_OPEN:
            if self.half_open_calls < self.half_open_max_calls:
                self.half_open_calls += 1
                return True
            return False
        
        # Circuit is OPEN
        return False
    
    def _update_state(self):
        """Update circuit state based on time and stats"""
        if self.state == CircuitState.OPEN:
            if self._time_since_state_change() > self.reset_timeout:
                print(f"[Circuit Breaker] '{self.name}' moving to HALF_OPEN state")
                self.state = CircuitState.HALF_OPEN
                self.last_state_change = datetime.now()
                self.half_open_calls = 0
    
    def _on_success(self):
        """Handle successful call"""
        self.stats.successful_calls += 1
        self.stats.consecutive_failures = 0
        
        if self.state == CircuitState.HALF_OPEN:
            print(f"[Circuit Breaker] '{self.name}' recovered, moving to CLOSED state")
            self.state = CircuitState.CLOSED
            self.last_state_change = datetime.now()
    
    def _on_failure(self):
        """Handle failed call"""
        self.stats.failed_calls += 1
        self.stats.consecutive_failures += 1
        self.stats.last_failure_time = datetime.now()
        
        if self.stats.consecutive_failures >= self.failure_threshold:
            if self.state != CircuitState.OPEN:
                print(f"[Circuit Breaker] '{self.name}' opening after {self.stats.consecutive_failures} failures")
                self.state = CircuitState.OPEN
                self.last_state_change = datetime.now()
    
    def _time_since_state_change(self) -> float:
        """Time in seconds since last state change"""
        return (datetime.now() - self.last_state_change).total_seconds()
    
    def _time_until_retry(self) -> float:
        """Time in seconds until circuit might close"""
        if self.state == CircuitState.OPEN:
            elapsed = self._time_since_state_change()
            return max(0, self.reset_timeout - elapsed)
        return 0
    
    def reset(self):
        """Manually reset the circuit breaker"""
        self.state = CircuitState.CLOSED
        self.stats = CircuitStats()
        self.last_state_change = datetime.now()
        self.half_open_calls = 0
        print(f"[Circuit Breaker] '{self.name}' manually reset")
    
    def get_status(self) -> dict:
        """Get current circuit breaker status"""
        return {
            'name': self.name,
            'state': self.state.value,
            'total_calls': self.stats.total_calls,
            'successful_calls': self.stats.successful_calls,
            'failed_calls': self.stats.failed_calls,
            'consecutive_failures': self.stats.consecutive_failures,
            'time_until_retry': self._time_until_retry() if self.state == CircuitState.OPEN else 0
        }

# Global circuit breakers for different services
circuits = {
    'llm_generation': CircuitBreaker('LLM Generation', failure_threshold=3, timeout=15),
    'xcode_build': CircuitBreaker('Xcode Build', failure_threshold=2, timeout=30),
    'simulator': CircuitBreaker('Simulator', failure_threshold=3, timeout=10)
}