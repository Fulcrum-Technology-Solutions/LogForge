"""Output adapter for sending logs to files."""

import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, TextIO, Dict, Any, Union

from logforge.outputs.base import OutputAdapter

logger = logging.getLogger(__name__)


class FileAdapter(OutputAdapter):
    """Output adapter for sending logs to a file."""
    
    def __init__(self, output_dir: str = "logs", base_filename: str = "logforge", 
                 default_extension: str = ".log", name: str = "file", 
                 mode: str = "a", max_size: int = None, 
                 backup_count: int = 5, hourly_rotation: bool = True,
                 data_source_field: str = None,
                 use_template_structure: bool = True,
                 custom_naming_pattern: str = None):
        """Initialize the file adapter.
        
        Args:
            output_dir: Directory where log files will be stored
            base_filename: Base name for log files (without extension)
            default_extension: Default file extension for logs
            name: The name of the adapter
            mode: The file mode (default 'a' for append)
            max_size: Maximum file size in bytes before rotation (default None for no rotation)
            backup_count: Number of backup files to keep (default 5)
            hourly_rotation: Whether to rotate files hourly (default True)
            data_source_field: Field in the log entry JSON to use for data source separation
                               (default None, no separation)
            use_template_structure: Whether to use template folder structure for naming (default True)
            custom_naming_pattern: Custom pattern for file naming (default None)
        """
        super().__init__(name)
        
        # Handle backward compatibility with file_path parameter
        if '/' in output_dir or '\\' in output_dir:
            # Looks like this might be a full path, split into directory and filename
            self.file_path = output_dir  # Store the original for backward compatibility
            output_dir = os.path.dirname(output_dir)
            filename_with_ext = os.path.basename(self.file_path)
            base_filename, ext = os.path.splitext(filename_with_ext)
            if ext:
                default_extension = ext
        else:
            # Construct file_path from components for backward compatibility
            self.file_path = os.path.join(output_dir, f"{base_filename}{default_extension}")
            
        self.output_dir = output_dir
        self.base_filename = base_filename
        self.default_extension = default_extension
        self.mode = mode
        self.max_size = max_size
        self.backup_count = backup_count
        self.hourly_rotation = hourly_rotation
        self.data_source_field = data_source_field
        self.use_template_structure = use_template_structure
        self.custom_naming_pattern = custom_naming_pattern
        
        # Dictionary to track files: {key: {"file": file_obj, "size": current_size}}
        self.files: Dict[str, Dict[str, Any]] = {}
        self.current_hour: Optional[int] = None
        
        # Ensure base directory exists
        os.makedirs(Path(output_dir).absolute(), exist_ok=True)
        
        # Initialize current hour
        if self.hourly_rotation:
            self.current_hour = datetime.now().hour
        
    def _get_file_key(self, data_source: str = None, file_extension: str = None) -> str:
        """Generate a unique key for file tracking.
        
        Args:
            data_source: The data source name
            file_extension: The file extension
            
        Returns:
            A unique key for tracking this file
        """
        key = data_source or '_default'
        if file_extension:
            # Strip leading dot if present
            ext = file_extension.lstrip('.') if file_extension.startswith('.') else file_extension
            key = f"{key}_{ext}"
        return key
        
    def _get_folder_structure(self, metadata: Dict[str, Any] = None) -> Optional[str]:
        """Extract the folder structure from template metadata.
        
        Args:
            metadata: The template metadata
            
        Returns:
            The folder structure string or None if not available
        """
        if not metadata or 'template_path' not in metadata:
            return None
            
        template_path = Path(metadata['template_path'])
        parts = template_path.parts
        
        # Skip 'templates' directory and the filename
        start_idx = 1 if parts and parts[0] == 'templates' else 0
        if len(parts) <= start_idx + 1:  # Need at least one folder component
            return None
            
        # Join relevant parts with underscores
        return '_'.join(parts[start_idx:-1]).lower()
        
    def _determine_extension(self, file_extension: str = None, metadata: Dict[str, Any] = None) -> str:
        """Determine the appropriate file extension.
        
        Args:
            file_extension: Explicitly provided file extension
            metadata: Template metadata
            
        Returns:
            The file extension to use
        """
        # 1. Explicitly provided extension
        if file_extension:
            # Ensure it has a leading dot
            return file_extension if file_extension.startswith('.') else f".{file_extension}"
            
        # 2. Format from metadata
        if metadata and 'format' in metadata:
            format_to_ext = {
                'json': '.json',
                'xml': '.xml',
                'text': '.txt',
                'csv': '.csv',
                'cef': '.log',
                'leef': '.log',
                'kv': '.log',
                'syslog': '.log'
            }
            format_value = metadata['format'].lower()
            if format_value in format_to_ext:
                return format_to_ext[format_value]
        
        # 3. Template extension (if available)
        if metadata and 'template_path' in metadata:
            template_path = Path(metadata['template_path'])
            # Skip .j2 extension
            if template_path.suffix == '.j2':
                # Get extension before .j2
                stem = template_path.stem
                ext = Path(stem).suffix
                if ext:
                    return ext
            elif template_path.suffix:
                return template_path.suffix
                
        # 4. Default extension
        return self.default_extension
    
    def _extract_data_source(self, log_entry: str, metadata: Dict[str, Any] = None) -> Optional[str]:
        """Extract the data source from the log entry or metadata.
        
        Args:
            log_entry: The log entry
            metadata: Template metadata
            
        Returns:
            The data source name or None if not found/applicable
        """
        # 1. First try to extract from metadata (preferred method)
        if metadata:
            # Direct generator name
            if 'generator' in metadata:
                return metadata['generator']
                
            # Construct from vendor/product/data_source
            if all(key in metadata for key in ['vendor', 'product', 'data_source']):
                vendor = metadata.get('vendor', '').lower()
                product = metadata.get('product', '').lower() 
                source = metadata.get('data_source', '').lower().replace(' ', '_')
                return f"{vendor}_{product}_{source}"
        
        # 2. Only fall back to JSON extraction if configured
        if not self.data_source_field:
            return None
            
        # 3. Try extracting from log content as last resort
        # Header line check
        if log_entry.startswith("GENERATOR:"):
            first_line = log_entry.split('\n')[0]
            return first_line.replace("GENERATOR:", "").strip()
        
        # JSON extraction attempt for JSON-looking content
        if log_entry.strip().startswith('{') and log_entry.strip().endswith('}'):
            try:
                import json
                # Remove control characters for safer parsing
                fixed_entry = ''.join(ch for ch in log_entry if ord(ch) >= 32 or ch == '\n')
                data = json.loads(fixed_entry)
                
                if self.data_source_field in data:
                    return str(data[self.data_source_field])
            except (json.JSONDecodeError, AttributeError, TypeError):
                pass
        
        # We couldn't determine the data source
        logger.debug("Could not determine data source from log entry or metadata")
        return None
    
    def _sanitize_filename(self, name: str) -> str:
        """Sanitize a name for safe use in filenames.
        
        Args:
            name: The name to sanitize
            
        Returns:
            A sanitized name safe for use in filenames
        """
        # Replace illegal filename characters with underscores
        return ''.join(c if c.isalnum() or c == '_' else '_' for c in name)
        
    def _get_file_path(self, data_source: str = None, file_extension: str = None, metadata: Dict[str, Any] = None) -> str:
        """Get the file path for the given data source and current time.
        
        Args:
            data_source: The data source name
            file_extension: The file extension to use (e.g., '.xml', '.json')
            metadata: Optional metadata from the template
            
        Returns:
            The file path
        """
        # Get the appropriate file extension
        output_extension = self._determine_extension(file_extension, metadata)
        
        # Determine effective data source name
        if self.use_template_structure:
            # Try to get folder structure from template path
            folder_structure = self._get_folder_structure(metadata)
            if folder_structure:
                effective_data_source = folder_structure
            else:
                effective_data_source = data_source if data_source else "default"
        else:
            # Use data source directly
            effective_data_source = data_source if data_source else "default"
            
        # Sanitize data source name
        effective_data_source = self._sanitize_filename(effective_data_source)
        
        # Add timestamp to filename if using hourly rotation
        if self.hourly_rotation:
            timestamp = datetime.now().strftime("%Y%m%d_%H")
            filename = f"{effective_data_source}_{timestamp}_{self.base_filename}{output_extension}"
        else:
            filename = f"{effective_data_source}_{self.base_filename}{output_extension}"
            
        # Create absolute path
        file_path = Path(self.output_dir) / filename
        return str(file_path)
    
    def _open_file(self, data_source: str = None, file_extension: str = None, metadata: Dict[str, Any] = None):
        """Open the file for writing.
        
        Args:
            data_source: The data source name
            file_extension: The file extension to use
            metadata: Optional metadata from the template
        """
        file_path = self._get_file_path(data_source, file_extension, metadata)
        key = self._get_file_key(data_source, file_extension)
        
        try:
            file_obj = open(file_path, self.mode, encoding='utf-8')
            # Get current size for file rotation if needed
            current_size = 0
            if self.max_size is not None:
                file_obj.seek(0, os.SEEK_END)
                current_size = file_obj.tell()
                
            self.files[key] = {"file": file_obj, "size": current_size}
            logger.debug(f"Opened file: {file_path}")
                
        except Exception as e:
            logger.error(f"Error opening file {file_path}: {e}")
            self.files[key] = {"file": None, "size": 0}
            
    def _rotate_file(self, data_source: str = None, file_extension: str = None, metadata: Dict[str, Any] = None):
        """Rotate the log file if it exceeds the maximum size.
        
        Args:
            data_source: The data source name
            file_extension: The file extension to use
            metadata: Optional metadata from the template
        """
        key = self._get_file_key(data_source, file_extension)
        file_path = self._get_file_path(data_source, file_extension, metadata)
        
        # Close the current file
        if key in self.files and self.files[key]["file"]:
            try:
                self.files[key]["file"].close()
            except Exception as e:
                logger.error(f"Error closing file {file_path}: {e}")
            self.files[key]["file"] = None
            
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
        self._open_file(data_source, file_extension, metadata)
        if key in self.files:
            self.files[key]["size"] = 0
    
    def _check_hour_rotation(self, data_source: str = None, file_extension: str = None, metadata: Dict[str, Any] = None):
        """Check if hourly rotation is needed and perform it if necessary.
        
        Args:
            data_source: The data source name
            file_extension: The file extension to use
            metadata: Optional metadata from the template
        """
        if not self.hourly_rotation:
            return
            
        current_hour = datetime.now().hour
        if current_hour != self.current_hour:
            self.current_hour = current_hour
            self._rotate_file(data_source, file_extension, metadata)
        
    def send_with_extension(self, log_entry: str, file_extension: str = None, metadata: Dict[str, Any] = None) -> bool:
        """Send a log entry to the file with specific file extension.
        
        Args:
            log_entry: The log entry to send
            file_extension: The file extension to use for the output file
            metadata: Optional metadata from the template
            
        Returns:
            True if the log entry was successfully sent, False otherwise
        """
        # Determine the data source
        data_source = self._extract_data_source(log_entry, metadata)
        
        # Generate a unique key for this file
        key = self._get_file_key(data_source, file_extension)
        
        # Check for hourly rotation
        self._check_hour_rotation(data_source, file_extension, metadata)
        
        # Open file if not already open
        if key not in self.files or not self.files[key]["file"]:
            self._open_file(data_source, file_extension, metadata)
        
        # Ensure file is available
        if key not in self.files or not self.files[key]["file"]:
            logger.error(f"File not open for data source {data_source}")
            return False
                
        try:
            # Add a newline if needed
            if not log_entry.endswith('\n'):
                log_entry += '\n'
                
            # Write to the file
            self.files[key]["file"].write(log_entry)
            self.files[key]["file"].flush()
            
            # Update current size for rotation
            if self.max_size is not None:
                self.files[key]["size"] += len(log_entry.encode('utf-8'))
                
                # Rotate if necessary
                if self.files[key]["size"] > self.max_size:
                    self._rotate_file(data_source, file_extension, metadata)
                    
            return True
            
        except Exception as e:
            logger.error(f"Error writing to file for data source {data_source}: {e}")
            return False
        
    def send(self, log_entry: str) -> bool:
        """Send a log entry to the file.
        
        Args:
            log_entry: The log entry to send
            
        Returns:
            True if the log entry was successfully sent, False otherwise
        """
        # Default to send without a specific file extension
        return self.send_with_extension(log_entry, None)
            
    def close(self):
        """Close all open files."""
        for key, file_info in self.files.items():
            if file_info["file"]:
                try:
                    file_info["file"].close()
                except Exception as e:
                    data_source = key.split('_')[0] if '_' in key else key
                    logger.error(f"Error closing file for data source {data_source}: {e}")
                    
        self.files.clear()