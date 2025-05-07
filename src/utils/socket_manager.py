import socket
import time
from contextlib import contextmanager

class SocketManager:
    """A manager for socket connections to prevent 'Address already in use' errors."""
    
    def __init__(self, timeout=10, max_retries=3):
        self.timeout = timeout
        self.max_retries = max_retries
        # Store the original socket.create_connection function
        self._original_create_connection = socket.create_connection
        # Apply our patched version
        self._patch_socket()
    
    def _patch_socket(self):
        """Patch the socket.create_connection function with our own implementation."""
        def patched_create_connection(*args, **kwargs):
            retry_delay = 1.0
            last_error = None
            
            for attempt in range(self.max_retries):
                try:
                    # Set a timeout for the connection attempt
                    if 'timeout' not in kwargs:
                        kwargs['timeout'] = self.timeout
                    return self._original_create_connection(*args, **kwargs)
                except socket.error as e:
                    last_error = e
                    if "Address already in use" in str(e):
                        print(f"Socket error in create_connection (attempt {attempt+1}/{self.max_retries}): {e}")
                        if attempt < self.max_retries - 1:
                            time.sleep(retry_delay)
                            retry_delay *= 2
                            continue
                    # For other errors, or if we've exhausted retries, re-raise
                    raise
            
            if last_error:
                raise last_error
            raise socket.error("Failed to create connection after multiple attempts")
        
        # Replace the original function with our patched version
        socket.create_connection = patched_create_connection
    
    def restore_socket(self):
        """Restore the original socket.create_connection function."""
        socket.create_connection = self._original_create_connection
    
    @contextmanager
    def patched_socket(self):
        """Context manager for temporarily patching socket."""
        try:
            self._patch_socket()
            yield
        finally:
            self.restore_socket()
