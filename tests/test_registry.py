"""Basic tests for entity registry."""

import pytest
from synth_logs.core.registry import EntityRegistry, User, Device, Service


def test_user_creation():
    """Test basic User creation."""
    user = User(username="testuser", full_name="Test User", email="test@example.com")
    assert user.username == "testuser"
    assert user.full_name == "Test User"
    assert user.email == "test@example.com"
    assert user.user_id is not None

def test_device_creation():
    """Test basic Device creation."""
    device = Device(hostname="test-host", ip_address="192.168.1.1", mac_address="00:11:22:33:44:55")
    assert device.hostname == "test-host"
    assert device.ip_address == "192.168.1.1"
    assert device.mac_address == "00:11:22:33:44:55"
    assert device.device_id is not None

def test_service_creation():
    """Test basic Service creation."""
    service = Service(name="test-service", port=8080, protocol="HTTP")
    assert service.name == "test-service"
    assert service.port == 8080
    assert service.protocol == "HTTP"
    assert service.service_id is not None

def test_registry_add_get():
    """Test adding and retrieving entities from registry."""
    registry = EntityRegistry()
    
    # Add entities
    user = User(username="testuser", full_name="Test User", email="test@example.com")
    device = Device(hostname="test-host", ip_address="192.168.1.1", mac_address="00:11:22:33:44:55")
    service = Service(name="test-service", port=8080, protocol="HTTP")
    
    registry.add_user(user)
    registry.add_device(device)
    registry.add_service(service)
    
    # Retrieve entities
    assert registry.get_user("testuser") == user
    assert registry.get_device("test-host") == device
    assert registry.get_service("test-service") == service
    
    # Test non-existent entities
    assert registry.get_user("nonexistent") is None
    assert registry.get_device("nonexistent") is None
    assert registry.get_service("nonexistent") is None