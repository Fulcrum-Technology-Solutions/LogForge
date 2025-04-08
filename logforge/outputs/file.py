"""Output adapter for sending logs to files."""

import logging
import os
import time
from datetime import datetime
from typing import Optional, TextIO, Dict, Any

from logforge.outputs.base import OutputAdapter

logger = logging.getLogger(__name__)


class FileAdapter(OutputAdapter):
    """Output adapter for sending logs to a file."""
    
    def __init__(self, output_dir: str = "logs", base_filename: str = "logforge", 
                 default_extension: str = ".log", name: str = "file", 
                 mode: str = "a", max_size: int = None, 
                 backup_count: int = 5, hourly_rotation: bool = True,
                 data_source_field: str = None):
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
        """
        super().__init__(name)
        
        # Handle backward compatibility with file_path parameter
        if '/' in output_dir or '\\' in output_dir:
            # Looks like this might be a full path, split into directory and filename
            self.file_path = output_dir  # Store the original for backward compatibility
            output_dir = os.path.dirname(output_dir)
            filename_with_ext = os.path.basename(output_dir)
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
        self.files: Dict[str, TextIO] = {}  # Dict of open files by data source
        self.current_sizes: Dict[str, int] = {}  # Dict of current file sizes by data source
        self.current_hour: Optional[int] = None
        
        # Ensure base directory exists
        os.makedirs(os.path.abspath(output_dir), exist_ok=True)
        
        # Initialize current hour
        if self.hourly_rotation:
            self.current_hour = datetime.now().hour
        
    def _get_file_path(self, data_source: str = None, file_extension: str = None, metadata: Dict[str, Any] = None) -> str:
        """Get the file path for the given data source and current time.
        
        Args:
            data_source: The data source name
            file_extension: The file extension to use (e.g., '.xml', '.json')
            metadata: Optional metadata from the template
            
        Returns:
            The file path
        """
        # Get folder structure from metadata if available, otherwise use data_source
        folder_structure = ""
        template_path = None
        if metadata and 'template_path' in metadata:
            template_path = metadata['template_path']
            # Extract folder structure from template path (templates/folder1/folder2/folder3/file.j2)
            # We want to create folder1_folder2_folder3
            parts = template_path.split('/')
            # Skip 'templates' and the actual filename
            if len(parts) > 2:
                # Check if parts[0] is 'templates', if so skip it
                start_idx = 1 if parts[0] == 'templates' else 0
                # Don't include the file part
                relevant_parts = parts[start_idx:-1]
                folder_structure = '_'.join(relevant_parts).lower()
        
        # Use the folder structure if available, otherwise fall back to data_source
        if folder_structure:
            effective_data_source = folder_structure
        else:
            effective_data_source = data_source if data_source else "default"
        
        # Sanitize data source name to avoid path issues
        effective_data_source = ''.join(c if c.isalnum() or c == '_' else '_' for c in effective_data_source)
        
        logger.debug(f"Getting file path for data source: {effective_data_source} from template: {template_path}")
        
        # Priority for file extension:
        # 1. Explicitly provided extension from config
        # 2. Extension from original template file path 
        # 3. Format specified in metadata
        # 4. Default extension from adapter config
        
        if file_extension:
            # 1. Use the provided extension
            output_extension = file_extension
        elif template_path and os.path.splitext(template_path)[1]:
            # 2. Use the extension from the template file (but not .j2)
            template_ext = os.path.splitext(template_path)[1]
            if template_ext == '.j2':
                # If template is .j2, try to look at the extension before .j2
                template_real_ext = os.path.splitext(os.path.splitext(template_path)[0])[1]
                if template_real_ext:
                    output_extension = template_real_ext
                else:
                    # Default to configured extension if can't determine
                    output_extension = self.default_extension
            else:
                output_extension = template_ext
        elif metadata and 'format' in metadata:
            # 3. Use format from metadata
            format_value = metadata['format'].lower()
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
            if format_value in format_to_ext:
                output_extension = format_to_ext[format_value]
            else:
                output_extension = self.default_extension
        else:
            # 4. Default to configured extension
            output_extension = self.default_extension
            
        # Add timestamp to filename if using hourly rotation
        if self.hourly_rotation:
            timestamp = datetime.now().strftime("%Y%m%d_%H")
            filename = f"{effective_data_source}_{timestamp}_{self.base_filename}{output_extension}"
        else:
            filename = f"{effective_data_source}_{self.base_filename}{output_extension}"
            
        return os.path.join(self.output_dir, filename)
    
    def _open_file(self, data_source: str = None, file_extension: str = None, metadata: Dict[str, Any] = None):
        """Open the file for writing.
        
        Args:
            data_source: The data source name
            file_extension: The file extension to use
            metadata: Optional metadata from the template
        """
        file_path = self._get_file_path(data_source, file_extension, metadata)
        key = data_source or '_default'
        if file_extension:
            key = f"{key}_{file_extension}"
        
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
            
    def _rotate_file(self, data_source: str = None, file_extension: str = None, metadata: Dict[str, Any] = None):
        """Rotate the log file if it exceeds the maximum size.
        
        Args:
            data_source: The data source name
            file_extension: The file extension to use
            metadata: Optional metadata from the template
        """
        key = data_source or '_default'
        if file_extension:
            key = f"{key}_{file_extension}"
            
        file_path = self._get_file_path(data_source, file_extension, metadata)
        
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
        self._open_file(data_source, file_extension, metadata)
        self.current_sizes[key] = 0
    
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
        logger.debug(f"Sending log entry to file with extension {file_extension}, length: {len(log_entry)}")
        
        # First try to extract data source from metadata if provided
        data_source = None
        if metadata:
            # Try to get consistent generator name from metadata
            if 'generator' in metadata:
                data_source = metadata['generator']
                logger.debug(f"Using generator name from metadata: {data_source}")
            # Construct from vendor/product/data_source if available
            elif all(key in metadata for key in ['vendor', 'product', 'data_source']):
                vendor = metadata.get('vendor', '').lower()
                product = metadata.get('product', '').lower() 
                source = metadata.get('data_source', '').lower().replace(' ', '_')
                data_source = f"{vendor}_{product}_{source}"
                data_source = ''.join(c if c.isalnum() or c == '_' else '_' for c in data_source)
                logger.debug(f"Constructed generator name from metadata: {data_source}")
        
        # Only try to extract from log entry if we couldn't get it from metadata
        if not data_source and self.data_source_field:
            data_source = self._extract_data_source(log_entry)
            logger.debug(f"Extracted data source from log content: {data_source}")
        
        key = data_source or '_default'
        
        # If using a specific extension, add it to the key
        if file_extension:
            key = f"{key}_{file_extension}"
        
        # Check for hourly rotation
        self._check_hour_rotation(data_source, file_extension, metadata)
        
        # Get the file path for debugging purposes
        file_path = self._get_file_path(data_source, file_extension, metadata)
        logger.debug(f"Using file path: {file_path}")
        
        # Open file if not already open
        if key not in self.files or not self.files[key]:
            logger.info(f"Opening file: {file_path}")
            self._open_file(data_source, file_extension, metadata)
        
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
                    self._rotate_file(data_source, file_extension, metadata)
                    
            return True
            
        except Exception as e:
            logger.error(f"Error writing to file for data source {data_source}: {e}")
            return False
    
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
        
        logger.debug(f"Extracting data source using field: {self.data_source_field}")
        
        # Fallback extraction using basic string search
        import re
        
        # Check for the GENERATOR: header line (our custom format)
        if log_entry.startswith("GENERATOR:"):
            first_line = log_entry.split('\n')[0]
            generator_name = first_line.replace("GENERATOR:", "").strip()
            logger.debug(f"Found generator in header line: {generator_name}")
            return generator_name
        
        # Try multiple patterns to find the generator field
        
        # Pattern 1: Look for "generator": "something" or 'generator': 'something'
        generator_pattern = r'"{}"\s*:\s*"([^"]+)"'.format(self.data_source_field)
        generator_matches = re.search(generator_pattern, log_entry)
        
        # Pattern 2: Look for generator name in a more specific format
        if not generator_matches:
            # Look for specific generator patterns in the content
            pattern_checks = [
                # Windows Security logs
                (r'microsoft_windows_security_([a-z_]+)', 'microsoft_windows_security_{}'),
                # Windows System logs
                (r'microsoft_windows_system_([a-z_]+)', 'microsoft_windows_system_{}'),
                # Windows Application logs
                (r'microsoft_windows_application_([a-z_]+)', 'microsoft_windows_application_{}'),
                # PaloAlto logs
                (r'paloalto_firewall_([a-z_]+)', 'paloalto_firewall_{}'),
                # Azure logs
                (r'azure_([a-z_]+)', 'azure_{}')
            ]
            
            for pattern, template in pattern_checks:
                matches = re.search(pattern, log_entry)
                if matches:
                    result = template.format(matches.group(1))
                    logger.debug(f"Found generator via pattern '{pattern}': {result}")
                    return result
        
        if generator_matches:
            # Extract the generator name from the regex match
            generator_name = generator_matches.group(1)
            logger.debug(f"Found generator name via regex: {generator_name}")
            
            # Clean up generator name for use in filenames
            for char in ['/', '\\', ':', '*', '?', '"', '<', '>', '|', ' ']:
                generator_name = generator_name.replace(char, '_')
            return generator_name
            
        # If regex fails, try JSON parsing as a backup (but only for JSON-looking content)
        if log_entry.strip().startswith('{') and log_entry.strip().endswith('}'):
            try:
                import json
                
                # Try to fix common JSON issues by removing control characters
                fixed_entry = ''.join(ch for ch in log_entry if ord(ch) >= 32 or ch == '\n')
                
                data = json.loads(fixed_entry)
                
                logger.debug(f"Log entry parsed as JSON with keys: {list(data.keys())}")
                
                if self.data_source_field in data:
                    # Clean up generator name for use in filenames
                    generator_name = str(data[self.data_source_field])
                    logger.debug(f"Found generator name via JSON: {generator_name}")
                    
                    # Replace special characters that shouldn't be in filenames
                    for char in ['/', '\\', ':', '*', '?', '"', '<', '>', '|', ' ']:
                        generator_name = generator_name.replace(char, '_')
                    return generator_name
                else:
                    logger.debug(f"Field '{self.data_source_field}' not found in JSON data")
            except (json.JSONDecodeError, AttributeError, TypeError) as e:
                # Log the error for debugging
                logger.debug(f"Could not extract data source from JSON-looking log entry: {e}")
        # Skip JSON parsing for non-JSON content
            
        # If we still don't have a data source, try to infer it from the log content
        # For example, look for specific patterns that might indicate the source
        
        # Identify Windows Event Logs
        if "Windows-Security-Auditing" in log_entry:
            # Extract Event ID if possible
            event_id_match = re.search(r'<EventID[^>]*>(\d+)</EventID>', log_entry)
            event_id = event_id_match.group(1) if event_id_match else None
            
            logger.debug(f"Found Windows Security Auditing event with ID: {event_id}")
            
            # Map Event IDs to generator types
            event_id_map = {
                "4624": "microsoft_windows_security_login_success",
                "4625": "microsoft_windows_security_login_failure",
                "4740": "microsoft_windows_security_account_locked",
                "4672": "microsoft_windows_security_privilege_use",
                "4688": "microsoft_windows_security_process_creation"
            }
            
            if event_id and event_id in event_id_map:
                return event_id_map[event_id]
            
            # Fallback to content-based checks
            elif "LogonType" in log_entry or "Logon Type" in log_entry:
                return "microsoft_windows_security_login_success"
            elif "Logon Failed" in log_entry:
                return "microsoft_windows_security_login_failure"
            elif "Account Locked" in log_entry:
                return "microsoft_windows_security_account_locked"
            elif "Privilege" in log_entry:
                return "microsoft_windows_security_privilege_use"
            elif "Process Creation" in log_entry:
                return "microsoft_windows_security_process_creation"
            else:
                return "microsoft_windows_security"
        
        # Identify Windows System Logs
        elif "Windows-System" in log_entry:
            if "Service Control Manager" in log_entry and "started" in log_entry:
                return "microsoft_windows_system_service_start"
            elif "Service Control Manager" in log_entry and "stopped" in log_entry:
                return "microsoft_windows_system_service_stop"
            elif "Time Service" in log_entry or "TimeChange" in log_entry:
                return "microsoft_windows_system_time_change"
            else:
                return "microsoft_windows_system"
        
        # Identify Windows Application Logs
        elif "Windows-Application" in log_entry or "Application Error" in log_entry:
            if "Error" in log_entry:
                return "microsoft_windows_application_error"
            elif "Warning" in log_entry:
                return "microsoft_windows_application_warning"
            elif "crash" in log_entry.lower() or "stopped working" in log_entry:
                return "microsoft_windows_application_crash"
            else:
                return "microsoft_windows_application_info"
                
        # Identify PaloAlto Logs
        elif "TRAFFIC" in log_entry:
            return "paloalto_firewall_traffic_session"
        elif "THREAT" in log_entry:
            return "paloalto_firewall_threat_alert"
        elif "paloalto" in log_entry.lower():
            return "paloalto_firewall"
        
        logger.warning(f"Could not extract or infer data source from log entry")
        logger.debug(f"Log entry content (first 100 chars): {log_entry[:100]}...")
            
        return None
        
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
        for key, file in self.files.items():
            if file:
                try:
                    file.close()
                except Exception as e:
                    data_source = key if key != '_default' else 'default'
                    logger.error(f"Error closing file for data source {data_source}: {e}")
                    
        self.files.clear()