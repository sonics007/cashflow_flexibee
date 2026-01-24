"""
Rate Limiter for FlexiBee API
Prevents overwhelming the FlexiBee server with too many requests
"""

import time
from threading import Lock
from collections import deque
from datetime import datetime, timedelta

class RateLimiter:
    """
    Token bucket rate limiter
    Ensures we don't exceed FlexiBee API rate limits
    """
    
    def __init__(self, max_requests=50, time_window=60):
        """
        Initialize rate limiter
        
        Args:
            max_requests: Maximum number of requests allowed
            time_window: Time window in seconds (default: 60s = 1 minute)
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = deque()
        self.lock = Lock()
    
    def acquire(self):
        """
        Acquire permission to make a request
        Blocks if rate limit is exceeded
        """
        with self.lock:
            now = datetime.now()
            
            # Remove old requests outside the time window
            cutoff = now - timedelta(seconds=self.time_window)
            while self.requests and self.requests[0] < cutoff:
                self.requests.popleft()
            
            # Check if we're at the limit
            if len(self.requests) >= self.max_requests:
                # Calculate how long to wait
                oldest_request = self.requests[0]
                wait_until = oldest_request + timedelta(seconds=self.time_window)
                wait_seconds = (wait_until - now).total_seconds()
                
                if wait_seconds > 0:
                    print(f"⏳ Rate limit reached. Waiting {wait_seconds:.1f}s...")
                    time.sleep(wait_seconds)
                    # Recursively try again
                    return self.acquire()
            
            # Record this request
            self.requests.append(now)
            return True
    
    def get_stats(self):
        """Get current rate limiter statistics"""
        with self.lock:
            now = datetime.now()
            cutoff = now - timedelta(seconds=self.time_window)
            
            # Clean old requests
            while self.requests and self.requests[0] < cutoff:
                self.requests.popleft()
            
            return {
                "requests_in_window": len(self.requests),
                "max_requests": self.max_requests,
                "time_window": self.time_window,
                "available_slots": self.max_requests - len(self.requests)
            }


class AdaptiveDelay:
    """
    Adaptive delay between requests
    Increases delay if errors occur, decreases if successful
    """
    
    def __init__(self, min_delay=0.1, max_delay=2.0, increase_factor=1.5, decrease_factor=0.9):
        """
        Initialize adaptive delay
        
        Args:
            min_delay: Minimum delay in seconds
            max_delay: Maximum delay in seconds
            increase_factor: Multiply delay by this on error
            decrease_factor: Multiply delay by this on success
        """
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.increase_factor = increase_factor
        self.decrease_factor = decrease_factor
        self.current_delay = min_delay
        self.lock = Lock()
    
    def wait(self):
        """Wait for the current delay period"""
        with self.lock:
            time.sleep(self.current_delay)
    
    def on_success(self):
        """Decrease delay after successful request"""
        with self.lock:
            self.current_delay = max(
                self.min_delay,
                self.current_delay * self.decrease_factor
            )
    
    def on_error(self):
        """Increase delay after failed request"""
        with self.lock:
            self.current_delay = min(
                self.max_delay,
                self.current_delay * self.increase_factor
            )
    
    def get_current_delay(self):
        """Get current delay value"""
        with self.lock:
            return self.current_delay


# Global rate limiter instance
# Default: 50 requests per minute (safe for most FlexiBee servers)
flexibee_rate_limiter = RateLimiter(max_requests=50, time_window=60)

# Global adaptive delay
flexibee_adaptive_delay = AdaptiveDelay(min_delay=0.1, max_delay=2.0)
