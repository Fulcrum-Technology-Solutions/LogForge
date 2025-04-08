"""Basic tests for templates module."""

from synth_logs.core.templates import TemplateManager


def test_template_manager_init():
    """Test TemplateManager initialization."""
    manager = TemplateManager()
    assert manager.template_dirs is not None
    assert manager.environment is not None


def test_random_guid():
    """Test random GUID generation."""
    manager = TemplateManager()
    guid = manager.random_guid()
    assert len(guid) == 36
    assert guid.count("-") == 4


def test_random_ip():
    """Test random IP generation."""
    manager = TemplateManager()
    ip = manager.random_ip()
    assert len(ip.split(".")) == 4


def test_random_private_ip():
    """Test random private IP generation."""
    manager = TemplateManager()
    ip = manager.random_private_ip()
    parts = ip.split(".")
    assert len(parts) == 4
    first_octet = int(parts[0])
    second_octet = int(parts[1])
    assert (first_octet == 10 or
            (first_octet == 172 and 16 <= second_octet <= 31) or
            (first_octet == 192 and second_octet == 168))


def test_template_manager_environment():
    """Test template manager environment setup."""
    manager = TemplateManager()
    
    # Check that the environment has the expected filters and globals
    assert 'random_guid' in manager.environment.filters
    assert 'random_ip' in manager.environment.filters
    assert 'random_private_ip' in manager.environment.filters
    
    # Test that globals are also registered
    assert 'random_guid' in manager.environment.globals
    assert 'random_ip' in manager.environment.globals