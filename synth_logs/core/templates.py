"""Template utilities for log generation."""

import datetime
import ipaddress
import logging
import os
import random
import string
import uuid
from typing import Dict, Any, Optional, List

import jinja2

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
        
    def _create_environment(self) -> jinja2.Environment:
        """Create a Jinja2 environment.
        
        Returns:
            A configured Jinja2 environment
        """
        loader = jinja2.FileSystemLoader(self.template_dirs)
        env = jinja2.Environment(loader=loader, autoescape=False)
        
        # Register custom filters
        env.filters['random_ip'] = self.random_ip
        env.filters['random_private_ip'] = self.random_private_ip
        env.filters['random_guid'] = self.random_guid
        env.filters['random_port'] = self.random_port
        env.filters['random_mac'] = self.random_mac
        env.filters['random_string'] = self.random_string
        env.filters['random_int'] = self.random_int
        env.filters['current_timestamp'] = self.current_timestamp
        env.filters['format_timestamp'] = self.format_timestamp
        
        # Register global functions (available directly in templates)
        env.globals['random_int'] = self.random_int
        env.globals['random_guid'] = self.random_guid
        env.globals['random_ip'] = self.random_ip
        env.globals['random_private_ip'] = self.random_private_ip
        env.globals['random_port'] = self.random_port
        env.globals['random_mac'] = self.random_mac
        env.globals['random_string'] = self.random_string
        env.globals['current_timestamp'] = self.current_timestamp
        env.globals['format_timestamp'] = self.format_timestamp
        
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