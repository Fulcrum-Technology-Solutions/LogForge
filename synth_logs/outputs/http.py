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
            
        # Log basic initialization at info level
        logger.info(f"Initializing HTTP adapter {name} for URL: {url}")
        
        # Log detailed configuration at debug level
        logger.debug(f"HTTP Method: {method}, Timeout: {timeout}s, Retry Count: {retry_count}, Retry Delay: {retry_delay}s")
        
        # Log headers with sensitive info masked at debug level
        header_str = ', '.join([
            f'{k}: {"*" * 10}' if k.lower() in ['authorization', 'x-api-key', 'api-key', 'apikey'] 
            else f'{k}: {v}' 
            for k, v in self.headers.items()
        ])
        logger.debug(f"HTTP Headers: {header_str}")
        
        # Validate URL format
        if not url.startswith(('http://', 'https://')):
            logger.warning(f"Invalid URL format: {url} - URL must start with http:// or https://")
        
        # Test connection on startup if not localhost
        if not (url.startswith('http://localhost') or url.startswith('http://127.0.0.1')):
            try:
                test_response = requests.head(
                    url,
                    timeout=timeout,
                    verify=verify_ssl,
                    allow_redirects=True
                )
                logger.info(f"Initial connection test to {url}: HTTP {test_response.status_code}")
            except requests.exceptions.RequestException as e:
                logger.warning(f"Initial connection test to {url} failed: {e}")
                self.last_error = str(e)
            
        # Initialize session for connection pooling
        self.session = requests.Session()
        
    def _handle_request_error(self, error, attempt, error_msg):
        """Handle request errors with consistent logging and retry logic.
        
        Args:
            error: The exception that occurred
            attempt: The current attempt number
            error_msg: Error message to log
            
        Returns:
            True if should retry, False if shouldn't retry
        """
        if attempt < self.retry_count:
            # This is a retry attempt
            logger.debug(f"{error_msg}, retrying in {self.retry_delay}s (attempt {attempt+1}/{self.retry_count})")
            time.sleep(self.retry_delay)
            return True
        else:
            # This was the final attempt
            self.failed_count += 1
            self.last_error = error_msg
            
            # Use warning level for final failures to ensure visibility
            logger.warning(f"{error_msg} - Failed after {self.retry_count} retries (total failures: {self.failed_count})")
            
            # For HTTP errors, log response content if available
            if isinstance(error, requests.exceptions.HTTPError) and hasattr(error, 'response') and error.response:
                try:
                    logger.debug(f"Response content: {error.response.text[:500]}")
                except:
                    pass
            return False
    
    def send(self, log_entry: str) -> bool:
        """Send a log entry via HTTP.
        
        Args:
            log_entry: The log entry to send
            
        Returns:
            True if the log entry was successfully sent, False otherwise
        """
        # Always wrap the raw event text in a JSON field called "event"
        data = {'event': log_entry}
        
        # Try to send the request with retries
        for attempt in range(self.retry_count + 1):
            try:
                # Keep operation details at debug level
                logger.debug(f"Sending log to {self.url} (attempt {attempt+1}/{self.retry_count+1})")
                
                response = self.session.request(
                    method=self.method,
                    url=self.url,
                    json=data,
                    headers=self.headers,
                    timeout=self.timeout,
                    verify=self.verify_ssl
                )
                
                response.raise_for_status()  # Raise an exception for HTTP errors
                
                # Update success metrics
                self.sent_count += 1
                self.last_success_time = time.time()
                
                # Only log occasionally for successful operations to reduce log volume
                if self.sent_count % 100 == 1:  # Log 1st, 101st, 201st, etc.
                    logger.info(f"Successfully sent log to {self.url} (status: {response.status_code}, total sent: {self.sent_count})")
                else:
                    logger.debug(f"Successfully sent log (status: {response.status_code})")
                    
                return True
                
            except requests.exceptions.ConnectionError as e:
                # Network problems, DNS failure, refused connection
                error_msg = f"Connection error to {self.url}: {e}"
                if not self._handle_request_error(e, attempt, error_msg):
                    return False
                
            except requests.exceptions.Timeout as e:
                # Timeout errors
                error_msg = f"Timeout connecting to {self.url} (timeout={self.timeout}s): {e}"
                if not self._handle_request_error(e, attempt, error_msg):
                    return False
                
            except requests.exceptions.HTTPError as e:
                # HTTP errors (4xx, 5xx responses)
                status_code = e.response.status_code if hasattr(e, 'response') and e.response else 'unknown'
                error_msg = f"HTTP error {status_code} from {self.url}: {e}"
                if not self._handle_request_error(e, attempt, error_msg):
                    return False
                
            except requests.exceptions.RequestException as e:
                # Catch-all for any other request-related errors
                error_msg = f"Error sending log to {self.url}: {e}"
                if not self._handle_request_error(e, attempt, error_msg):
                    return False
                    
    def send_with_extension(self, log_entry: str, file_extension: str = None, metadata: Dict[str, Any] = None) -> bool:
        """Send a log entry with a specific file extension.
        
        Args:
            log_entry: The log entry to send
            file_extension: The extension of the source file
            metadata: Optional metadata from the template
            
        Returns:
            True if the log entry was successfully sent, False otherwise
        """
        # Create JSON object with event content
        data = {
            'event': log_entry,
        }
        
        # Add format info from metadata or file extension
        format_value = 'unknown'
        if metadata and 'format' in metadata:
            format_value = metadata['format'].lower()
        elif file_extension:
            format_value = file_extension.lstrip('.')
            
        data['format'] = format_value
        logger.debug(f"Setting format to '{format_value}' for log entry")
        
        # Try to send the request with retries
        for attempt in range(self.retry_count + 1):
            try:
                # Keep operation details at debug level
                logger.debug(f"Sending log to {self.url} with format {data['format']} (attempt {attempt+1}/{self.retry_count+1})")
                
                response = self.session.request(
                    method=self.method,
                    url=self.url,
                    json=data,
                    headers=self.headers,
                    timeout=self.timeout,
                    verify=self.verify_ssl
                )
                
                response.raise_for_status()  # Raise an exception for HTTP errors
                
                # Update success metrics
                self.sent_count += 1
                self.last_success_time = time.time()
                
                # Only log occasionally for successful operations to reduce log volume
                if self.sent_count % 100 == 1:  # Log 1st, 101st, 201st, etc.
                    logger.info(f"Successfully sent log to {self.url} (status: {response.status_code}, total sent: {self.sent_count})")
                else:
                    logger.debug(f"Successfully sent log with format {data['format']} (status: {response.status_code})")
                    
                return True
                
            except requests.exceptions.ConnectionError as e:
                # Network problems, DNS failure, refused connection
                error_msg = f"Connection error to {self.url}: {e}"
                if not self._handle_request_error(e, attempt, error_msg):
                    return False
                
            except requests.exceptions.Timeout as e:
                # Timeout errors
                error_msg = f"Timeout connecting to {self.url} (timeout={self.timeout}s): {e}"
                if not self._handle_request_error(e, attempt, error_msg):
                    return False
                
            except requests.exceptions.HTTPError as e:
                # HTTP errors (4xx, 5xx responses)
                status_code = e.response.status_code if hasattr(e, 'response') and e.response else 'unknown'
                error_msg = f"HTTP error {status_code} from {self.url}: {e}"
                if not self._handle_request_error(e, attempt, error_msg):
                    return False
                
            except requests.exceptions.RequestException as e:
                # Catch-all for any other request-related errors
                error_msg = f"Error sending log to {self.url}: {e}"
                if not self._handle_request_error(e, attempt, error_msg):
                    return False
        
    def get_status(self) -> str:
        """Get the status of the HTTP adapter.
        
        Returns:
            String describing the current status
        """
        # Log detailed status information at debug level
        if self.sent_count > 0 or self.failed_count > 0:
            logger.debug(f"HTTP adapter status for {self.url}: {self.sent_count} sent, {self.failed_count} failed")
            if self.last_error:
                logger.debug(f"Last error: {self.last_error}")
        
        # Return user-friendly status string
        if self.sent_count == 0 and self.failed_count == 0:
            return f"No logs sent yet to {self.url}"
        elif self.failed_count == 0:
            return f"Healthy - {self.sent_count} logs sent successfully to {self.url}"
        else:
            error_ratio = (self.failed_count / (self.sent_count + self.failed_count)) * 100
            status = f"Warning - {self.sent_count} success, {self.failed_count} failures ({error_ratio:.1f}%)"
            if self.last_error:
                # Truncate long error messages for display
                error_summary = self.last_error[:100] + "..." if len(self.last_error) > 100 else self.last_error
                status += f" - Last error: {error_summary}"
            return status
    
    def close(self):
        """Close the HTTP adapter."""
        if self.session:
            try:
                self.session.close()
                # Only log detailed status info if we actually sent any logs
                if self.sent_count > 0 or self.failed_count > 0:
                    logger.info(f"HTTP adapter {self.name} closed. Final status: {self.get_status()}")
                else:
                    logger.debug(f"HTTP adapter {self.name} closed without sending any logs")
            except Exception as e:
                logger.warning(f"Error closing HTTP session: {e}")