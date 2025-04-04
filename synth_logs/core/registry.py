"""Entity registry for managing users, devices, services, and other entities."""

import json
import logging
import os
import uuid
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Set, Any, Union

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
    os_type: Optional[str] = None
    os_version: Optional[str] = None
    owner: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation.
        
        Returns:
            Dictionary representation of the device
        """
        return asdict(self)


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
                
            # Load users
            for user_data in data.get('users', []):
                self.add_user(User(**user_data))
                
            # Load devices
            for device_data in data.get('devices', []):
                self.add_device(Device(**device_data))
                
            # Load services
            for service_data in data.get('services', []):
                self.add_service(Service(**service_data))
                
            logger.info(f"Loaded {len(data.get('users', []))} users, "
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
        
        data = {
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
                
            logger.info(f"Saved {len(self.users)} users, {len(self.devices)} devices, "
                        f"and {len(self.services)} services to {file_path}")
                        
        except Exception as e:
            logger.error(f"Error saving entities to {file_path}: {e}")