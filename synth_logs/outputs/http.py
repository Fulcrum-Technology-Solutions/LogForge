"""Output adapter for sending logs via HTTP."""

import json
import logging
import time
from typing import Dict, Any, Optional, List

import requests

from synth_logs.outputs.base import OutputAdapter

logger = logging.getLogger(__name__)


class HttpAdapter(OutputAdapter):
    """Output adapter for sending logs via HTTP."""
    
    def __init__(self, url: str, name: str = "http", 
                 method: str = "POST", headers: Dict[str, str] = None,
                 retry_count: int = 3, retry_delay: float = 1.0,
                 timeout: float = 10.0, verify_ssl: bool = True):
        """Initialize the HTTP adapter.
        
        Args:
            url: The URL to send logs to
            name: The name of the adapter
            method: The HTTP method to use (default POST)
            headers: Additional HTTP headers to include
            retry_count: Number of retries on failure (default 3)
            retry_delay: Delay between retries in seconds (default 1.0)
            timeout: Timeout for HTTP requests in seconds (default 10.0)
            verify_ssl: Whether to verify SSL certificates (default True)
        """
        super().__init__(name)
        self.url = url
        self.method = method.upper()
        self.headers = headers or {}
        self.retry_count = retry_count
        self.retry_delay = retry_delay
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        
        # Set default headers if not provided
        if 'Content-Type' not in self.headers:
            self.headers['Content-Type'] = 'application/json'
            
        # Initialize session for connection pooling
        self.session = requests.Session()
        
    def send(self, log_entry: str) -> bool:
        """Send a log entry via HTTP.
        
        Args:
            log_entry: The log entry to send
            
        Returns:
            True if the log entry was successfully sent, False otherwise
        """
        # Determine if log_entry is JSON or plain text
        data = log_entry
        try:
            # If it's valid JSON, parse it so requests sends it as JSON
            if self.headers.get('Content-Type') == 'application/json':
                data = json.loads(log_entry)
        except json.JSONDecodeError:
            # Not valid JSON, send as plain text
            if self.headers.get('Content-Type') == 'application/json':
                # Wrap in a simple JSON envelope
                data = {'message': log_entry}
                
        # Try to send the request with retries
        for attempt in range(self.retry_count + 1):
            try:
                response = self.session.request(
                    method=self.method,
                    url=self.url,
                    json=data if isinstance(data, dict) else None,
                    data=log_entry if not isinstance(data, dict) else None,
                    headers=self.headers,
                    timeout=self.timeout,
                    verify=self.verify_ssl
                )
                
                response.raise_for_status()  # Raise an exception for HTTP errors
                return True
                
            except requests.exceptions.RequestException as e:
                if attempt < self.retry_count:
                    logger.warning(f"Error sending log to {self.url}, retrying in {self.retry_delay}s: {e}")
                    time.sleep(self.retry_delay)
                else:
                    logger.error(f"Failed to send log to {self.url} after {self.retry_count} retries: {e}")
                    return False
                    
    def close(self):
        """Close the HTTP adapter."""
        if self.session:
            try:
                self.session.close()
            except Exception as e:
                logger.error(f"Error closing HTTP session: {e}")