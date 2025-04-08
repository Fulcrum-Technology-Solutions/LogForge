"""Tests for the entity registry module."""

import os
import tempfile
import pytest
import yaml
import json
from synth_logs.core.registry import EntityRegistry, User, Device, Service


class TestEntityClasses:
    """Test the entity dataclasses."""
    
    def test_user_creation(self):
        """Test creating a User object."""
        user = User(
            username="testuser",
            full_name="Test User",
            email="test@example.com",
            department="IT",
            title="Engineer",
            is_admin=False
        )
        
        assert user.username == "testuser"
        assert user.full_name == "Test User"
        assert user.email == "test@example.com"
        assert user.department == "IT"
        assert user.title == "Engineer"
        assert user.is_admin is False
        assert user.user_id is not None  # Should generate a UUID
        
    def test_user_to_dict(self):
        """Test User to_dict method."""
        user = User(
            username="testuser",
            full_name="Test User",
            email="test@example.com"
        )
        
        user_dict = user.to_dict()
        assert isinstance(user_dict, dict)
        assert user_dict["username"] == "testuser"
        assert user_dict["full_name"] == "Test User"
        assert user_dict["email"] == "test@example.com"
        
    def test_device_creation(self):
        """Test creating a Device object."""
        device = Device(
            hostname="testhost",
            ip_address="192.168.1.100",
            mac_address="00:11:22:33:44:55",
            os_type="Windows",
            os_version="10"
        )
        
        assert device.hostname == "testhost"
        assert device.ip_address == "192.168.1.100"
        assert device.mac_address == "00:11:22:33:44:55"
        assert device.os_type == "Windows"
        assert device.os_version == "10"
        assert device.device_id is not None  # Should generate a UUID
        
    def test_service_creation(self):
        """Test creating a Service object."""
        service = Service(
            name="test-service",
            port=8080,
            protocol="HTTP",
            description="Test service"
        )
        
        assert service.name == "test-service"
        assert service.port == 8080
        assert service.protocol == "HTTP"
        assert service.description == "Test service"
        assert service.service_id is not None  # Should generate a UUID


class TestEntityRegistry:
    """Test the EntityRegistry class."""
    
    def test_registry_init(self):
        """Test initializing an EntityRegistry."""
        registry = EntityRegistry()
        assert len(registry.users) == 0
        assert len(registry.devices) == 0
        assert len(registry.services) == 0
        
    def test_add_user(self):
        """Test adding a user to the registry."""
        registry = EntityRegistry()
        user = User(
            username="testuser",
            full_name="Test User",
            email="test@example.com"
        )
        
        registry.add_user(user)
        assert len(registry.users) == 1
        assert registry.users["testuser"] == user
        
    def test_add_device(self):
        """Test adding a device to the registry."""
        registry = EntityRegistry()
        device = Device(
            hostname="testhost",
            ip_address="192.168.1.100",
            mac_address="00:11:22:33:44:55"
        )
        
        registry.add_device(device)
        assert len(registry.devices) == 1
        assert registry.devices["testhost"] == device
        
    def test_add_service(self):
        """Test adding a service to the registry."""
        registry = EntityRegistry()
        service = Service(
            name="test-service",
            port=8080,
            protocol="HTTP"
        )
        
        registry.add_service(service)
        assert len(registry.services) == 1
        assert registry.services["test-service"] == service
        
    def test_get_user(self):
        """Test getting a user from the registry."""
        registry = EntityRegistry()
        user = User(
            username="testuser",
            full_name="Test User",
            email="test@example.com"
        )
        
        registry.add_user(user)
        retrieved_user = registry.get_user("testuser")
        assert retrieved_user == user
        assert registry.get_user("nonexistent") is None
        
    def test_get_device(self):
        """Test getting a device from the registry."""
        registry = EntityRegistry()
        device = Device(
            hostname="testhost",
            ip_address="192.168.1.100",
            mac_address="00:11:22:33:44:55"
        )
        
        registry.add_device(device)
        retrieved_device = registry.get_device("testhost")
        assert retrieved_device == device
        assert registry.get_device("nonexistent") is None
        
    def test_get_service(self):
        """Test getting a service from the registry."""
        registry = EntityRegistry()
        service = Service(
            name="test-service",
            port=8080,
            protocol="HTTP"
        )
        
        registry.add_service(service)
        retrieved_service = registry.get_service("test-service")
        assert retrieved_service == service
        assert registry.get_service("nonexistent") is None
        
    def test_get_random_user(self):
        """Test getting a random user from the registry."""
        registry = EntityRegistry()
        
        # Empty registry should return None
        assert registry.get_random_user() is None
        
        # Add a user and ensure it's returned
        user = User(
            username="testuser",
            full_name="Test User",
            email="test@example.com"
        )
        registry.add_user(user)
        
        assert registry.get_random_user() == user
        
    def test_load_from_yaml_file(self):
        """Test loading entities from a YAML file."""
        registry = EntityRegistry()
        
        # Create a temporary YAML file
        with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as temp_file:
            yaml_content = {
                "users": [
                    {
                        "username": "testuser",
                        "full_name": "Test User",
                        "email": "test@example.com"
                    }
                ],
                "devices": [
                    {
                        "hostname": "testhost",
                        "ip_address": "192.168.1.100",
                        "mac_address": "00:11:22:33:44:55"
                    }
                ],
                "services": [
                    {
                        "name": "test-service",
                        "port": 8080,
                        "protocol": "HTTP"
                    }
                ]
            }
            yaml.dump(yaml_content, temp_file)
            temp_file_path = temp_file.name
        
        try:
            # Load entities from the file
            registry.load_from_file(temp_file_path)
            
            # Verify the entities were loaded
            assert len(registry.users) == 1
            assert "testuser" in registry.users
            assert registry.users["testuser"].full_name == "Test User"
            
            assert len(registry.devices) == 1
            assert "testhost" in registry.devices
            assert registry.devices["testhost"].ip_address == "192.168.1.100"
            
            assert len(registry.services) == 1
            assert "test-service" in registry.services
            assert registry.services["test-service"].port == 8080
        finally:
            # Clean up the temporary file
            os.unlink(temp_file_path)
            
    def test_load_from_json_file(self):
        """Test loading entities from a JSON file."""
        registry = EntityRegistry()
        
        # Create a temporary JSON file
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as temp_file:
            json_content = {
                "users": [
                    {
                        "username": "testuser",
                        "full_name": "Test User",
                        "email": "test@example.com"
                    }
                ],
                "devices": [
                    {
                        "hostname": "testhost",
                        "ip_address": "192.168.1.100",
                        "mac_address": "00:11:22:33:44:55"
                    }
                ],
                "services": [
                    {
                        "name": "test-service",
                        "port": 8080,
                        "protocol": "HTTP"
                    }
                ]
            }
            temp_file.write(json.dumps(json_content).encode())
            temp_file_path = temp_file.name
        
        try:
            # Load entities from the file
            registry.load_from_file(temp_file_path)
            
            # Verify the entities were loaded
            assert len(registry.users) == 1
            assert "testuser" in registry.users
            assert registry.users["testuser"].full_name == "Test User"
        finally:
            # Clean up the temporary file
            os.unlink(temp_file_path)
            
    def test_save_to_yaml_file(self):
        """Test saving entities to a YAML file."""
        registry = EntityRegistry()
        
        # Add some entities
        registry.add_user(User(
            username="testuser",
            full_name="Test User",
            email="test@example.com"
        ))
        
        registry.add_device(Device(
            hostname="testhost",
            ip_address="192.168.1.100",
            mac_address="00:11:22:33:44:55"
        ))
        
        registry.add_service(Service(
            name="test-service",
            port=8080,
            protocol="HTTP"
        ))
        
        # Create a temporary file path
        with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as temp_file:
            temp_file_path = temp_file.name
        
        try:
            # Save the registry to the file
            registry.save_to_file(temp_file_path)
            
            # Load the file and verify its contents
            with open(temp_file_path, "r") as f:
                data = yaml.safe_load(f)
                
            assert len(data["users"]) == 1
            assert data["users"][0]["username"] == "testuser"
            assert data["users"][0]["full_name"] == "Test User"
            
            assert len(data["devices"]) == 1
            assert data["devices"][0]["hostname"] == "testhost"
            
            assert len(data["services"]) == 1
            assert data["services"][0]["name"] == "test-service"
        finally:
            # Clean up the temporary file
            os.unlink(temp_file_path)