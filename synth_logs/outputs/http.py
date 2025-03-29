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
        
        # For tracking number of sent/failed logs
        self.sent_count = 0
        self.failed_count = 0
        self.last_error = None
        self.last_success_time = None
        
        # Set default headers if not provided
        if 'Content-Type' not in self.headers:
            self.headers['Content-Type'] = 'application/json'
            
        # Log the configuration
        logger.warning(f"Initializing HTTP adapter {name} for URL: {url}")
        logger.warning(f"HTTP Method: {method}, Timeout: {timeout}s, Retry Count: {retry_count}")
        
        # Log headers with sensitive info masked
        header_str = ', '.join([
            f'{k}: {"*" * 10}' if k.lower() in ['authorization', 'x-api-key', 'api-key', 'apikey'] 
            else f'{k}: {v}' 
            for k, v in self.headers.items()
        ])
        logger.warning(f"HTTP Headers: {header_str}")
        
        # Validate URL format
        if not url.startswith(('http://', 'https://')):
            logger.error(f"Invalid URL format: {url} - URL must start with http:// or https://")
        
        # Test connection on startup if not localhost
        if not (url.startswith('http://localhost') or url.startswith('http://127.0.0.1')):
            try:
                test_response = requests.head(
                    url,
                    timeout=timeout,
                    verify=verify_ssl,
                    allow_redirects=True
                )
                logger.warning(f"Initial connection test to {url}: HTTP {test_response.status_code}")
            except requests.exceptions.RequestException as e:
                logger.error(f"Initial connection test to {url} failed: {e}")
                self.last_error = str(e)
            
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
                # Log sending attempt (debug level to avoid excessive logging)
                logger.debug(f"Sending log to {self.url} (attempt {attempt+1}/{self.retry_count+1})")
                
                # Extract a small part of the log for debugging
                log_preview = log_entry[:100] + '...' if len(log_entry) > 100 else log_entry
                logger.debug(f"Log content preview: {log_preview}")
                
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
                
                # Log successful send
                self.sent_count += 1
                self.last_success_time = time.time()
                
                # Only log every 100 successful requests to avoid log flooding
                if self.sent_count % 100 == 1:  # Log 1st, 101st, 201st, etc.
                    logger.warning(f"Successfully sent log to {self.url} (status: {response.status_code}, total sent: {self.sent_count})")
                else:
                    logger.debug(f"Successfully sent log to {self.url} (status: {response.status_code}, total sent: {self.sent_count})")
                    
                return True
                
            except requests.exceptions.ConnectionError as e:
                # Connection errors: network problems, DNS failure, refused connection
                error_msg = f"Connection error to {self.url}: {e}"
                if attempt < self.retry_count:
                    logger.warning(f"{error_msg}, retrying in {self.retry_delay}s (attempt {attempt+1}/{self.retry_count})")
                    time.sleep(self.retry_delay)
                else:
                    self.failed_count += 1
                    self.last_error = error_msg
                    logger.error(f"{error_msg} - Failed after {self.retry_count} retries (total failures: {self.failed_count})")
                    return False
            except requests.exceptions.Timeout as e:
                # Timeout errors
                error_msg = f"Timeout connecting to {self.url} (timeout={self.timeout}s): {e}"
                if attempt < self.retry_count:
                    logger.warning(f"{error_msg}, retrying in {self.retry_delay}s (attempt {attempt+1}/{self.retry_count})")
                    time.sleep(self.retry_delay)
                else:
                    self.failed_count += 1
                    self.last_error = error_msg
                    logger.error(f"{error_msg} - Failed after {self.retry_count} retries (total failures: {self.failed_count})")
                    return False
            except requests.exceptions.HTTPError as e:
                # HTTP errors (4xx, 5xx responses)
                status_code = e.response.status_code if hasattr(e, 'response') and e.response else 'unknown'
                error_msg = f"HTTP error {status_code} from {self.url}: {e}"
                if attempt < self.retry_count:
                    logger.warning(f"{error_msg}, retrying in {self.retry_delay}s (attempt {attempt+1}/{self.retry_count})")
                    time.sleep(self.retry_delay)
                else:
                    self.failed_count += 1
                    self.last_error = error_msg
                    logger.error(f"{error_msg} - Failed after {self.retry_count} retries (total failures: {self.failed_count})")
                    # Log response content if available for debugging
                    if hasattr(e, 'response') and e.response:
                        try:
                            logger.error(f"Response content: {e.response.text[:500]}")
                        except:
                            pass
                    return False
            except requests.exceptions.RequestException as e:
                # Catch-all for any other request-related errors
                error_msg = f"Error sending log to {self.url}: {e}"
                if attempt < self.retry_count:
                    logger.warning(f"{error_msg}, retrying in {self.retry_delay}s (attempt {attempt+1}/{self.retry_count})")
                    time.sleep(self.retry_delay)
                else:
                    self.failed_count += 1
                    self.last_error = error_msg
                    logger.error(f"{error_msg} - Failed after {self.retry_count} retries (total failures: {self.failed_count})")
                    return False
                    
    def send_with_extension(self, log_entry: str, file_extension: str = None) -> bool:
        """Send a log entry with a specific file extension.
        
        Args:
            log_entry: The log entry to send
            file_extension: The extension of the source file (not used for HTTP)
            
        Returns:
            True if the log entry was successfully sent, False otherwise
        """
        # HTTP adapter doesn't care about the file extension,
        # so just forward to the regular send method
        return self.send(log_entry)
        
    def get_status(self) -> str:
        """Get the status of the HTTP adapter.
        
        Returns:
            String describing the current status
        """
        if self.sent_count == 0 and self.failed_count == 0:
            return f"No logs sent yet to {self.url}"
        elif self.failed_count == 0:
            return f"Healthy - {self.sent_count} logs sent successfully to {self.url}"
        else:
            error_ratio = (self.failed_count / (self.sent_count + self.failed_count)) * 100
            status = f"Warning - {self.sent_count} success, {self.failed_count} failures ({error_ratio:.1f}%)"
            if self.last_error:
                status += f" - Last error: {self.last_error}"
            return status
    
    def close(self):
        """Close the HTTP adapter."""
        if self.session:
            try:
                self.session.close()
                logger.info(f"HTTP adapter {self.name} closed. Final status: {self.get_status()}")
            except Exception as e:
                logger.error(f"Error closing HTTP session: {e}")