"""Template utilities for log generation."""

import datetime
import ipaddress
import logging
import os
import random
import string
import uuid
import glob
from typing import Dict, Any, Optional, List, Tuple

import jinja2
import yaml

from synth_logs.core.registry import EntityRegistry

logger = logging.getLogger(__name__)


class TemplateManager:
    """Manager for log templates."""
    
    def __init__(self, template_dirs: Optional[List[str]] = None):
        """Initialize the template manager.
        
        Args:
            template_dirs: Directories to search for templates (defaults to 'templates' directory)
        """
        if template_dirs is None:
            # Default to 'templates' directory relative to this file
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            template_dirs = [os.path.join(base_dir, 'templates')]
            
        self.template_dirs = template_dirs
        self.environment = self._create_environment()
        self.metadata_cache = {}
        
    def _create_environment(self) -> jinja2.Environment:
        """Create a Jinja2 environment.
        
        Returns:
            A configured Jinja2 environment
        """
        loader = jinja2.FileSystemLoader(self.template_dirs)
        env = jinja2.Environment(loader=loader, autoescape=False)
        
        # Register custom filters
        env.filters['random_ip'] = self.random_ip
        env.filters['random_public_ip'] = self.random_ip  # Alias for random_ip
        env.filters['random_private_ip'] = self.random_private_ip
        env.filters['random_guid'] = self.random_guid
        env.filters['random_port'] = self.random_port
        env.filters['random_mac'] = self.random_mac
        env.filters['random_string'] = self.random_string
        env.filters['random_int'] = self.random_int
        env.filters['random_number'] = self.random_int  # Alias for random_int
        env.filters['current_timestamp'] = self.current_timestamp
        env.filters['format_timestamp'] = self.format_timestamp
        env.filters['to_datetime'] = self.to_datetime
        env.filters['format_datetime'] = self.format_datetime
        
        # Add string formatting filters
        env.filters['format'] = lambda value, fmt: format(value, fmt)
        env.filters['hex'] = lambda value: format(value, 'x')
        
        # Register global functions (available directly in templates)
        env.globals['random_int'] = self.random_int
        env.globals['random_number'] = self.random_int  # Alias for random_int
        env.globals['random_guid'] = self.random_guid
        env.globals['random_ip'] = self.random_ip
        env.globals['random_public_ip'] = self.random_ip  # Alias for random_ip
        env.globals['random_private_ip'] = self.random_private_ip
        env.globals['random_port'] = self.random_port
        env.globals['random_mac'] = self.random_mac
        env.globals['random_string'] = self.random_string
        env.globals['current_timestamp'] = self.current_timestamp
        env.globals['format_timestamp'] = self.format_timestamp
        env.globals['to_datetime'] = self.to_datetime
        env.globals['format_datetime'] = self.format_datetime
        
        return env
        
    def render_template(self, template_path: str, registry: EntityRegistry, context: Dict[str, Any] = None) -> str:
        """Render a template.
        
        Args:
            template_path: Path to the template (relative to template_dirs)
            registry: Entity registry to provide to the template
            context: Additional context variables for the template
            
        Returns:
            The rendered template
        """
        try:
            template = self.environment.get_template(template_path)
            
            # Create a context with the registry and additional context
            full_context = {
                'registry': registry,
                'random': random,
                'uuid': uuid,
                'datetime': datetime,
                # Add helper functions directly
                'random_int': self.random_int,
                'random_guid': self.random_guid,
                'random_ip': self.random_ip,
                'random_private_ip': self.random_private_ip,
                'random_port': self.random_port,
                'random_mac': self.random_mac,
                'random_string': self.random_string,
                'current_timestamp': self.current_timestamp,
                'format_timestamp': self.format_timestamp,
            }
            
            if context:
                full_context.update(context)
                
            return template.render(**full_context)
        except Exception as e:
            logger.error(f"Error rendering template {template_path}: {e}")
            return f"ERROR: Failed to render template {template_path}: {e}"
            
    @staticmethod
    def random_guid() -> str:
        """Generate a random GUID.
        
        Returns:
            A random GUID
        """
        return str(uuid.uuid4())
        
    @staticmethod
    def random_ip() -> str:
        """Generate a random public IP address.
        
        Returns:
            A random public IP address
        """
        # Generate a random public IP (non-private, non-reserved)
        while True:
            ip = ipaddress.IPv4Address(random.randint(0, 2**32 - 1))
            if not ip.is_private and not ip.is_reserved:
                return str(ip)
                
    @staticmethod
    def random_private_ip() -> str:
        """Generate a random private IP address.
        
        Returns:
            A random private IP address
        """
        # Generate a random private IP from common private ranges
        private_ranges = [
            ('10.0.0.0', '10.255.255.255'),        # 10.0.0.0/8
            ('172.16.0.0', '172.31.255.255'),      # 172.16.0.0/12
            ('192.168.0.0', '192.168.255.255')     # 192.168.0.0/16
        ]
        
        start, end = random.choice(private_ranges)
        start_int = int(ipaddress.IPv4Address(start))
        end_int = int(ipaddress.IPv4Address(end))
        
        ip_int = random.randint(start_int, end_int)
        return str(ipaddress.IPv4Address(ip_int))
        
    @staticmethod
    def random_port(min_port: int = 1024, max_port: int = 65535) -> int:
        """Generate a random port number.
        
        Args:
            min_port: Minimum port number (default 1024)
            max_port: Maximum port number (default 65535)
            
        Returns:
            A random port number
        """
        return random.randint(min_port, max_port)
        
    @staticmethod
    def random_mac() -> str:
        """Generate a random MAC address.
        
        Returns:
            A random MAC address
        """
        mac = [random.randint(0x00, 0xff) for _ in range(6)]
        return ':'.join([f'{x:02x}' for x in mac])
        
    @staticmethod
    def random_string(length: int = 10, chars: str = None) -> str:
        """Generate a random string.
        
        Args:
            length: Length of the string (default 10)
            chars: Characters to use (default alphanumeric)
            
        Returns:
            A random string
        """
        if chars is None:
            chars = string.ascii_letters + string.digits
            
        return ''.join(random.choice(chars) for _ in range(length))
        
    @staticmethod
    def random_int(min_value: int = 0, max_value: int = 1000) -> int:
        """Generate a random integer.
        
        Args:
            min_value: Minimum value (default 0)
            max_value: Maximum value (default 1000)
            
        Returns:
            A random integer
        """
        return random.randint(min_value, max_value)
        
    @staticmethod
    def to_datetime(timestamp: str) -> datetime.datetime:
        """Convert a timestamp string to a datetime object.
        
        Args:
            timestamp: The timestamp string to convert
            
        Returns:
            A datetime object
        """
        try:
            # Try to parse the timestamp as ISO format
            return datetime.datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        except ValueError:
            # Fall back to current time
            return datetime.datetime.now()
            
    @staticmethod
    def format_datetime(dt: datetime.datetime, format_str: str = '%Y-%m-%dT%H:%M:%S.%fZ') -> str:
        """Format a datetime object.
        
        Args:
            dt: The datetime object to format
            format_str: The format string to use (default ISO format)
            
        Returns:
            The formatted timestamp
        """
        return dt.strftime(format_str)
        return random.randint(min_value, max_value)
        
    @staticmethod
    def current_timestamp() -> float:
        """Get the current timestamp.
        
        Returns:
            The current timestamp in seconds since epoch
        """
        return datetime.datetime.now().timestamp()
        
    @staticmethod
    def format_timestamp(timestamp: Optional[float] = None, format_str: str = '%Y-%m-%d %H:%M:%S') -> str:
        """Format a timestamp.
        
        Args:
            timestamp: The timestamp to format (default current time)
            format_str: The format string (default '%Y-%m-%d %H:%M:%S')
            
        Returns:
            The formatted timestamp
        """
        if timestamp is None:
            dt = datetime.datetime.now()
        else:
            dt = datetime.datetime.fromtimestamp(timestamp)
            
        return dt.strftime(format_str)
        
    def get_template_metadata(self, template_path: str) -> Dict[str, Any]:
        """Get metadata for a template.
        
        Args:
            template_path: Path to the template (relative to template_dirs)
            
        Returns:
            Dictionary containing template metadata
        """
        # If we have the metadata in the cache, return it
        if template_path in self.metadata_cache:
            return self.metadata_cache[template_path]
            
        # Look for a .meta.yaml file next to the template
        metadata = {}
        for template_dir in self.template_dirs:
            full_path = os.path.join(template_dir, template_path)
            meta_path = os.path.splitext(full_path)[0] + '.meta.yaml'
            
            if os.path.exists(meta_path):
                try:
                    with open(meta_path, 'r') as f:
                        metadata = yaml.safe_load(f) or {}
                    break
                except Exception as e:
                    logger.error(f"Error loading metadata for {template_path}: {e}")
                    
        # Set default metadata if not provided
        if not metadata:
            # Extract the product name and type from the path
            parts = template_path.split('/')
            if len(parts) >= 2:
                vendor = parts[0]
                product = parts[1] if len(parts) > 1 else ''
                event_type = os.path.splitext(os.path.basename(template_path))[0]
                
                metadata = {
                    'vendor': vendor.title(),
                    'product': product.title(),
                    'data_source': event_type.replace('_', ' ').title(),
                    'description': f'{vendor.title()} {product.title()} {event_type.replace("_", " ").title()} Events'
                }
                
        # Cache the metadata
        self.metadata_cache[template_path] = metadata
        return metadata
        
    def discover_templates(self) -> Dict[str, Dict[str, List[Dict[str, Any]]]]:
        """Discover all available templates and their metadata.
        
        Returns:
            A nested dictionary of vendors -> products -> template metadata
        """
        templates = {}
        
        for template_dir in self.template_dirs:
            if not os.path.exists(template_dir):
                continue
                
            # Walk the template directory
            for root, _, files in os.walk(template_dir):
                for file in files:
                    # Skip metadata files
                    if file.endswith('.meta.yaml'):
                        continue
                        
                    # Get the relative path to the template
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, template_dir)
                    
                    # Get metadata for the template
                    metadata = self.get_template_metadata(rel_path)
                    
                    vendor = metadata.get('vendor', 'Unknown')
                    product = metadata.get('product', 'Unknown')
                    
                    # Add the template to the dictionary
                    if vendor not in templates:
                        templates[vendor] = {}
                    if product not in templates[vendor]:
                        templates[vendor][product] = []
                        
                    template_info = {
                        'path': rel_path,
                        'data_source': metadata.get('data_source', 'Unknown'),
                        'description': metadata.get('description', ''),
                        'metadata': metadata
                    }
                    
                    templates[vendor][product].append(template_info)
                    
        return templates
        
    def get_all_template_paths(self) -> List[str]:
        """Get all template paths in the template directories.
        
        Returns:
            List of template paths
        """
        template_paths = []
        
        for template_dir in self.template_dirs:
            if not os.path.exists(template_dir):
                continue
                
            # Walk the template directory
            for root, _, files in os.walk(template_dir):
                for file in files:
                    # Skip metadata files
                    if file.endswith('.meta.yaml'):
                        continue
                        
                    # Get the relative path to the template
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, template_dir)
                    template_paths.append(rel_path)
        
        return template_paths
        
    def create_metadata_file(self, template_path: str, metadata: Dict[str, Any]) -> bool:
        """Create or update a metadata file for a template.
        
        Args:
            template_path: Path to the template (relative to template_dirs)
            metadata: Dictionary containing template metadata
            
        Returns:
            True if the metadata file was created/updated successfully, False otherwise
        """
        for template_dir in self.template_dirs:
            full_path = os.path.join(template_dir, template_path)
            if os.path.exists(full_path):
                meta_path = os.path.splitext(full_path)[0] + '.meta.yaml'
                
                try:
                    # Ensure directory exists
                    os.makedirs(os.path.dirname(meta_path), exist_ok=True)
                    
                    # Write the metadata file
                    with open(meta_path, 'w') as f:
                        yaml.dump(metadata, f, default_flow_style=False)
                        
                    # Update the cache
                    self.metadata_cache[template_path] = metadata
                    return True
                except Exception as e:
                    logger.error(f"Error creating metadata file for {template_path}: {e}")
                    return False
                    
        logger.error(f"Template path not found: {template_path}")
        return False