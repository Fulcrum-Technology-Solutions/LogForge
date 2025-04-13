"""Entity registry for managing users, devices, services, and other entities."""

import json
import logging
import os
import uuid
import ipaddress
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Set, Any, Union, Tuple

import yaml

logger = logging.getLogger(__name__)


@dataclass
class User:
    """Representation of a user entity."""
    
    username: str
    full_name: str
    email: str
    user_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    department: Optional[str] = None
    title: Optional[str] = None
    is_admin: bool = False
    employee_type: Optional[str] = None
    organization: Optional[str] = None
    location: Optional[Dict[str, str]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation.
        
        Returns:
            Dictionary representation of the user
        """
        return asdict(self)
        
    def __post_init__(self):
        """Convert location dict to proper format if needed."""
        if self.location is None:
            self.location = {}


@dataclass
class Device:
    """Representation of a device entity."""
    
    hostname: str
    ip_address: str
    mac_address: str
    device_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    fqdn: Optional[str] = None
    os_type: Optional[str] = None
    os_version: Optional[str] = None
    os: Optional[str] = None
    owner: Optional[str] = None
    device_type: Optional[str] = None
    model: Optional[str] = None
    department: Optional[str] = None
    status: Optional[str] = None
    last_updated: Optional[str] = None
    
    # This will hold any custom fields
    _custom_fields: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Process any additional fields after initialization."""
        # If fqdn is not provided but hostname exists, default it based on a domain from the first device
        if self.fqdn is None and self.hostname:
            # Don't set a default FQDN - just leave it as None if not provided
            pass
            
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation.
        
        Returns:
            Dictionary representation of the device including custom fields
        """
        # Start with the standard fields
        result = asdict(self)
        
        # Remove the internal _custom_fields from the result
        result.pop('_custom_fields', None)
        
        # Add all custom fields to the result
        result.update(self._custom_fields)
        
        return result
        
    def __setattr__(self, name: str, value: Any):
        """Custom attribute setter to handle custom fields.
        
        Args:
            name: The attribute name
            value: The attribute value
        """
        if name.startswith('custom_'):
            # Store in the custom fields dictionary
            self._custom_fields[name] = value
        else:
            # Set as a regular attribute
            super().__setattr__(name, value)


@dataclass
class Service:
    """Representation of a service entity."""
    
    name: str
    port: int
    protocol: str
    service_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    description: Optional[str] = None
    owner: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation.
        
        Returns:
            Dictionary representation of the service
        """
        return asdict(self)


class EntityRegistry:
    """Registry for entities like users, devices, and services."""
    
    def __init__(self):
        """Initialize the entity registry."""
        self.users: Dict[str, User] = {}
        self.devices: Dict[str, Device] = {}
        self.services: Dict[str, Service] = {}
        self.network_ranges: List[Tuple] = []
        
    def add_user(self, user: User):
        """Add a user to the registry.
        
        Args:
            user: The user to add
        """
        self.users[user.username] = user
        
    def add_device(self, device: Device):
        """Add a device to the registry.
        
        Args:
            device: The device to add
        """
        self.devices[device.hostname] = device
        
    def add_service(self, service: Service):
        """Add a service to the registry.
        
        Args:
            service: The service to add
        """
        self.services[service.name] = service
        
    def get_user(self, username: str) -> Optional[User]:
        """Get a user by username.
        
        Args:
            username: The username of the user to get
            
        Returns:
            The user, or None if not found
        """
        return self.users.get(username)
        
    def get_device(self, hostname: str) -> Optional[Device]:
        """Get a device by hostname.
        
        Args:
            hostname: The hostname of the device to get
            
        Returns:
            The device, or None if not found
        """
        return self.devices.get(hostname)
        
    def get_service(self, name: str) -> Optional[Service]:
        """Get a service by name.
        
        Args:
            name: The name of the service to get
            
        Returns:
            The service, or None if not found
        """
        return self.services.get(name)
        
    def get_random_user(self) -> Optional[User]:
        """Get a random user from the registry.
        
        Returns:
            A random user, or None if no users are registered
        """
        if not self.users:
            return None
            
        import random
        return random.choice(list(self.users.values()))
        
    def get_random_device(self) -> Optional[Device]:
        """Get a random device from the registry.
        
        Returns:
            A random device, or None if no devices are registered
        """
        if not self.devices:
            return None
            
        import random
        return random.choice(list(self.devices.values()))
        
    def get_random_service(self) -> Optional[Service]:
        """Get a random service from the registry.
        
        Returns:
            A random service, or None if no services are registered
        """
        if not self.services:
            return None
            
        import random
        return random.choice(list(self.services.values()))
    
    def get_network_ranges(self) -> List[Tuple]:
        """Get the network ranges.
        
        Returns:
            List of network range tuples (either CIDR notation or start/end IPs)
        """
        if not self.network_ranges:
            # Return default network ranges if none are configured
            return [
                ('10.0.0.0', '10.255.255.255'),       # 10.0.0.0/8
                ('172.16.0.0', '172.31.255.255'),     # 172.16.0.0/12
                ('192.168.0.0', '192.168.255.255')    # 192.168.0.0/16
            ]
        return self.network_ranges
        
    def load_from_file(self, file_path: str):
        """Load entities from a file.
        
        Args:
            file_path: The path to the file to load from
        """
        if not os.path.exists(file_path):
            logger.warning(f"Entity file not found: {file_path}")
            return
            
        file_ext = os.path.splitext(file_path)[1].lower()
        
        try:
            if file_ext == '.json':
                with open(file_path, 'r') as f:
                    data = json.load(f)
            elif file_ext in ('.yaml', '.yml'):
                with open(file_path, 'r') as f:
                    data = yaml.safe_load(f)
            else:
                logger.error(f"Unsupported file type: {file_ext}")
                return
            
            # Load network ranges
            network_ranges = []
            for range_config in data.get('network_ranges', []):
                # Handle CIDR notation
                cidr = range_config.get('cidr')
                if cidr:
                    try:
                        # Validate CIDR
                        network = ipaddress.IPv4Network(cidr)
                        name = range_config.get('name')
                        
                        # Add to network ranges - we'll pass the CIDR string directly
                        if name:
                            network_ranges.append((cidr, name))
                        else:
                            network_ranges.append((cidr,))
                    except ValueError as e:
                        logger.error(f"Invalid CIDR notation in network range: {e}")
                    continue
                    
                # Handle start/end IP notation
                start_ip = range_config.get('start_ip')
                end_ip = range_config.get('end_ip')
                name = range_config.get('name')
                
                if start_ip and end_ip:
                    try:
                        # Validate IP addresses
                        ipaddress.IPv4Address(start_ip)
                        ipaddress.IPv4Address(end_ip)
                        
                        # Add to network ranges
                        if name:
                            network_ranges.append((start_ip, end_ip, name))
                        else:
                            network_ranges.append((start_ip, end_ip))
                    except ValueError as e:
                        logger.error(f"Invalid IP address in network range: {e}")
            
            # Set network ranges in registry
            self.network_ranges = network_ranges
                
            # Load users
            for user_data in data.get('users', []):
                self.add_user(User(**user_data))
                
            # Load devices
            for device_data in data.get('devices', []):
                # Add default IP and MAC if not present
                if 'ip_address' not in device_data:
                    # Generate a random private IP
                    import random
                    ip_parts = [10, random.randint(0, 255), random.randint(0, 255), random.randint(1, 254)]
                    device_data['ip_address'] = '.'.join(str(part) for part in ip_parts)
                    
                if 'mac_address' not in device_data:
                    # Generate a random MAC address
                    import random
                    mac = [random.randint(0x00, 0xff) for _ in range(6)]
                    device_data['mac_address'] = ':'.join([f'{x:02x}' for x in mac])
                
                # Separate standard fields from custom fields
                standard_fields = {}
                custom_fields = {}
                
                for key, value in device_data.items():
                    if key.startswith('custom_'):
                        custom_fields[key] = value
                    else:
                        standard_fields[key] = value
                
                # Create the device with standard fields
                device = Device(**standard_fields)
                
                # Add custom fields
                for key, value in custom_fields.items():
                    setattr(device, key, value)
                
                self.add_device(device)
                
            # Load services
            for service_data in data.get('services', []):
                self.add_service(Service(**service_data))
                
            logger.info(f"Loaded {len(data.get('network_ranges', []))} network ranges, "
                        f"{len(data.get('users', []))} users, "
                        f"{len(data.get('devices', []))} devices, and "
                        f"{len(data.get('services', []))} services from {file_path}")
                        
        except Exception as e:
            logger.error(f"Error loading entities from {file_path}: {e}")
            
    def save_to_file(self, file_path: str):
        """Save entities to a file.
        
        Args:
            file_path: The path to the file to save to
        """
        file_ext = os.path.splitext(file_path)[1].lower()
        
        # Convert network ranges to a format suitable for serialization
        network_ranges_data = []
        for range_info in self.network_ranges:
            if len(range_info) > 0 and '/' in range_info[0]:  # CIDR notation
                entry = {'cidr': range_info[0]}
                if len(range_info) > 1:  # Has a name
                    entry['name'] = range_info[1]
                network_ranges_data.append(entry)
            elif len(range_info) >= 2:  # Start/end IP format
                entry = {'start_ip': range_info[0], 'end_ip': range_info[1]}
                if len(range_info) > 2:  # Has a name
                    entry['name'] = range_info[2]
                network_ranges_data.append(entry)
        
        data = {
            'network_ranges': network_ranges_data,
            'users': [user.to_dict() for user in self.users.values()],
            'devices': [device.to_dict() for device in self.devices.values()],
            'services': [service.to_dict() for service in self.services.values()],
        }
        
        try:
            if file_ext == '.json':
                with open(file_path, 'w') as f:
                    json.dump(data, f, indent=2)
            elif file_ext in ('.yaml', '.yml'):
                with open(file_path, 'w') as f:
                    yaml.dump(data, f)
            else:
                logger.error(f"Unsupported file type: {file_ext}")
                return
                
            logger.info(f"Saved {len(network_ranges_data)} network ranges, "
                        f"{len(self.users)} users, {len(self.devices)} devices, "
                        f"and {len(self.services)} services to {file_path}")
                        
        except Exception as e:
            logger.error(f"Error saving entities to {file_path}: {e}")