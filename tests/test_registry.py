"""Tests for entity registry."""

import pytest
from logforge.core.registry import EntityRegistry, User, Device, Service, Organization


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
    
def test_organization_creation():
    """Test basic Organization creation."""
    org = Organization(
        name="Test Corp",
        domain="testcorp.com",
        netbios_domain="TESTCORP",
        timezone="America/New_York",
        industry="Technology"
    )
    assert org.name == "Test Corp"
    assert org.domain == "testcorp.com"
    assert org.netbios_domain == "TESTCORP"
    assert org.timezone == "America/New_York"
    assert org.industry == "Technology"
    
def test_device_custom_fields():
    """Test device custom fields."""
    device = Device(
        hostname="test-host", 
        ip_address="192.168.1.1", 
        mac_address="00:11:22:33:44:55"
    )
    
    # Add custom fields
    device.custom_location = "Building A, Room 101"
    device.custom_asset_tag = "AST12345"
    
    # Access custom fields
    assert device.custom_location == "Building A, Room 101"
    assert device.custom_asset_tag == "AST12345"
    
    # Test __contains__ method (used for "is defined" checks in templates)
    assert "custom_location" in device
    assert "custom_asset_tag" in device
    assert "custom_nonexistent" not in device
    
def test_device_to_dict_with_custom_fields():
    """Test Device.to_dict() method with custom fields."""
    device = Device(
        hostname="test-host", 
        ip_address="192.168.1.1", 
        mac_address="00:11:22:33:44:55"
    )
    device.custom_location = "Building A, Room 101"
    
    device_dict = device.to_dict()
    assert "custom_location" in device_dict
    assert device_dict["custom_location"] == "Building A, Room 101"
    assert "_custom_fields" not in device_dict  # Ensure internal dict isn't included
    
def test_registry_organization_functions():
    """Test organization-related functions in registry."""
    registry = EntityRegistry()
    
    # Initially, organization is None
    assert registry.get_organization() is None
    
    # Default values when organization is not set
    assert registry.get_domain() == "example.com"
    assert registry.get_netbios_domain() == "EXAMPLE"
    assert registry.get_org_setting("password_expiry_days", 90) == 90
    
    # Set organization with settings
    org = Organization(
        name="Test Corp",
        domain="testcorp.com",
        netbios_domain="TESTCORP",
        settings={"password_expiry_days": 60, "account_lockout_threshold": 5}
    )
    registry.organization = org
    
    # Test retrieving organization data
    assert registry.get_organization() == org
    assert registry.get_domain() == "testcorp.com"
    assert registry.get_netbios_domain() == "TESTCORP"
    assert registry.get_org_setting("password_expiry_days", 90) == 60
    assert registry.get_org_setting("account_lockout_threshold", 3) == 5
    assert registry.get_org_setting("nonexistent", "default") == "default"
    
def test_device_fqdn_from_organization():
    """Test setting device FQDN based on organization domain."""
    registry = EntityRegistry()
    
    # Set organization with domain
    org = Organization(
        name="Test Corp",
        domain="testcorp.com"
    )
    registry.organization = org
    
    # Create a device without FQDN
    device_data = {
        "hostname": "test-host", 
        "ip_address": "192.168.1.1", 
        "mac_address": "00:11:22:33:44:55"
    }
    
    # Add it to registry
    # Normally this happens in load_from_file, but we're testing directly
    device = Device(**device_data)
    # Manually set FQDN as registry.load_from_file would
    if not device.fqdn and device.hostname and registry.organization and registry.organization.domain:
        device.fqdn = f"{device.hostname}.{registry.organization.domain}"
    
    registry.add_device(device)
    
    # Verify FQDN was set
    retrieved_device = registry.get_device("test-host")
    assert retrieved_device.fqdn == "test-host.testcorp.com"
    
def test_load_organization_from_file(tmpdir):
    """Test loading organization data from a YAML file."""
    # Create a test YAML file with organization data
    yaml_content = """
    organization:
      name: Test Organization
      domain: test.org
      netbios_domain: TESTORG
      timezone: America/Chicago
      settings:
        password_expiry_days: 45
        require_mfa: true
    users:
      - username: testuser
        full_name: Test User
        email: testuser@test.org
    devices:
      - hostname: testhost
        ip_address: 192.168.1.100
        mac_address: 00:11:22:33:44:55
    """
    
    # Write the test file
    test_file = tmpdir.join("test_entities.yaml")
    test_file.write(yaml_content)
    
    # Create registry and load the file
    registry = EntityRegistry()
    registry.load_from_file(str(test_file))
    
    # Verify organization data was loaded
    org = registry.get_organization()
    assert org is not None
    assert org.name == "Test Organization"
    assert org.domain == "test.org"
    assert org.netbios_domain == "TESTORG"
    
    # Verify settings
    assert registry.get_org_setting("password_expiry_days") == 45
    assert registry.get_org_setting("require_mfa") is True
    
    # Verify user data
    user = registry.get_user("testuser")
    assert user is not None
    assert user.full_name == "Test User"
    
    # Verify device data and FQDN auto-generation
    device = registry.get_device("testhost")
    assert device is not None
    assert device.ip_address == "192.168.1.100"
    # FQDN should be auto-generated based on org domain
    assert device.fqdn == "testhost.test.org"