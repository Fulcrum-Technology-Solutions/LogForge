"""Output adapter for sending logs to files."""

import logging
import os
import time
from datetime import datetime
from typing import Optional, TextIO, Dict

from synth_logs.outputs.base import OutputAdapter

logger = logging.getLogger(__name__)


class FileAdapter(OutputAdapter):
    """Output adapter for sending logs to a file."""
    
    def __init__(self, file_path: str, name: str = "file", 
                 mode: str = "a", max_size: int = None, 
                 backup_count: int = 5, hourly_rotation: bool = True,
                 data_source_field: str = None):
        """Initialize the file adapter.
        
        Args:
            file_path: The path to the file to write to
            name: The name of the adapter
            mode: The file mode (default 'a' for append)
            max_size: Maximum file size in bytes before rotation (default None for no rotation)
            backup_count: Number of backup files to keep (default 5)
            hourly_rotation: Whether to rotate files hourly (default True)
            data_source_field: Field in the log entry JSON to use for data source separation
                               (default None, no separation)
        """
        super().__init__(name)
        self.file_path = file_path
        self.mode = mode
        self.max_size = max_size
        self.backup_count = backup_count
        self.hourly_rotation = hourly_rotation
        self.data_source_field = data_source_field
        self.files: Dict[str, TextIO] = {}  # Dict of open files by data source
        self.current_sizes: Dict[str, int] = {}  # Dict of current file sizes by data source
        self.current_hour: Optional[int] = None
        
        # Ensure base directory exists
        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
        
        # Initialize current hour
        if self.hourly_rotation:
            self.current_hour = datetime.now().hour
        
    def _get_file_path(self, data_source: str = None) -> str:
        """Get the file path for the given data source and current time.
        
        Args:
            data_source: The data source name
            
        Returns:
            The file path
        """
        base_dir = os.path.dirname(os.path.abspath(self.file_path))
        base_name = os.path.basename(self.file_path)
        
        # Use a default name if data source is not provided
        effective_data_source = data_source if data_source else "default"
        
        logger.info(f"Getting file path for data source: {effective_data_source}")
        
        # Add timestamp to filename if using hourly rotation
        if self.hourly_rotation:
            timestamp = datetime.now().strftime("%Y%m%d_%H")
            return os.path.join(base_dir, f"{effective_data_source}_{timestamp}_{base_name}")
        else:
            return os.path.join(base_dir, f"{effective_data_source}_{base_name}")
    
    def _open_file(self, data_source: str = None):
        """Open the file for writing.
        
        Args:
            data_source: The data source name
        """
        file_path = self._get_file_path(data_source)
        key = data_source or '_default'
        
        try:
            self.files[key] = open(file_path, self.mode, encoding='utf-8')
            
            # Get current size for file rotation
            if self.max_size is not None:
                self.files[key].seek(0, os.SEEK_END)
                self.current_sizes[key] = self.files[key].tell()
            else:
                self.current_sizes[key] = 0
                
        except Exception as e:
            logger.error(f"Error opening file {file_path}: {e}")
            self.files[key] = None
            
    def _rotate_file(self, data_source: str = None):
        """Rotate the log file if it exceeds the maximum size.
        
        Args:
            data_source: The data source name
        """
        key = data_source or '_default'
        file_path = self._get_file_path(data_source)
        
        # Close the current file
        if key in self.files and self.files[key]:
            try:
                self.files[key].close()
            except Exception as e:
                logger.error(f"Error closing file {file_path}: {e}")
            self.files[key] = None
            
        # Rotate the backup files (only for size-based rotation)
        if not self.hourly_rotation:
            for i in range(self.backup_count - 1, 0, -1):
                src = f"{file_path}.{i}"
                dst = f"{file_path}.{i+1}"
                
                if os.path.exists(src):
                    if os.path.exists(dst):
                        os.remove(dst)
                    os.rename(src, dst)
                    
            # Rename the current file
            if os.path.exists(file_path):
                dst = f"{file_path}.1"
                if os.path.exists(dst):
                    os.remove(dst)
                os.rename(file_path, dst)
            
        # Open a new file
        self._open_file(data_source)
        self.current_sizes[key] = 0
    
    def _check_hour_rotation(self, data_source: str = None):
        """Check if hourly rotation is needed and perform it if necessary.
        
        Args:
            data_source: The data source name
        """
        if not self.hourly_rotation:
            return
            
        current_hour = datetime.now().hour
        if current_hour != self.current_hour:
            self.current_hour = current_hour
            self._rotate_file(data_source)
        
    def _extract_data_source(self, log_entry: str) -> Optional[str]:
        """Extract the data source from the log entry.
        
        Args:
            log_entry: The log entry
            
        Returns:
            The data source name or None if not found/applicable
        """
        if not self.data_source_field:
            logger.info(f"No data source field configured.")
            return None
        
        logger.info(f"Extracting data source using field: {self.data_source_field}")
            
        # Simple check for JSON format with data source field
        try:
            import json
            data = json.loads(log_entry)
            
            logger.info(f"Log entry parsed as JSON with keys: {list(data.keys())}")
            
            if self.data_source_field in data:
                # Clean up generator name for use in filenames
                generator_name = str(data[self.data_source_field])
                logger.info(f"Found generator name: {generator_name}")
                
                # Replace special characters that shouldn't be in filenames
                for char in ['/', '\\', ':', '*', '?', '"', '<', '>', '|', ' ']:
                    generator_name = generator_name.replace(char, '_')
                return generator_name
            else:
                logger.info(f"Field '{self.data_source_field}' not found in JSON data")
        except (json.JSONDecodeError, AttributeError, TypeError) as e:
            # Log the error for debugging
            logger.warning(f"Could not extract data source from log entry: {e}")
            logger.debug(f"Log entry content (first 100 chars): {log_entry[:100]}...")
            
        return None
        
    def send(self, log_entry: str) -> bool:
        """Send a log entry to the file.
        
        Args:
            log_entry: The log entry to send
            
        Returns:
            True if the log entry was successfully sent, False otherwise
        """
        logger.info(f"Sending log entry to file, length: {len(log_entry)}")
        
        # Extract data source if configured
        data_source = self._extract_data_source(log_entry)
        logger.info(f"Extracted data source: {data_source}")
        
        key = data_source or '_default'
        
        # Check for hourly rotation
        self._check_hour_rotation(data_source)
        
        # Get the file path for debugging purposes
        file_path = self._get_file_path(data_source)
        logger.info(f"Using file path: {file_path}")
        
        # Open file if not already open
        if key not in self.files or not self.files[key]:
            logger.info(f"Opening file for data source: {data_source}")
            self._open_file(data_source)
        
        if not self.files.get(key):
            logger.error(f"File not open for data source {data_source}")
            return False
                
        try:
            # Add a newline if needed
            if not log_entry.endswith('\n'):
                log_entry += '\n'
                
            # Write to the file
            self.files[key].write(log_entry)
            self.files[key].flush()
            
            # Update current size for rotation
            if self.max_size is not None:
                self.current_sizes[key] = self.current_sizes.get(key, 0) + len(log_entry.encode('utf-8'))
                
                # Rotate if necessary
                if self.current_sizes[key] > self.max_size:
                    self._rotate_file(data_source)
                    
            return True
            
        except Exception as e:
            logger.error(f"Error writing to file for data source {data_source}: {e}")
            return False
            
    def close(self):
        """Close all open files."""
        for key, file in self.files.items():
            if file:
                try:
                    file.close()
                except Exception as e:
                    data_source = key if key != '_default' else 'default'
                    logger.error(f"Error closing file for data source {data_source}: {e}")
                    
        self.files.clear()