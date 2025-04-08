"""Pytest configuration for LogForge tests."""

import os
import pytest
import tempfile
import shutil
import yaml


@pytest.fixture(scope="session")
def temp_dir():
    """Create a temporary directory for test files."""
    dir_path = tempfile.mkdtemp()
    yield dir_path
    shutil.rmtree(dir_path)


@pytest.fixture
def sample_config_file(temp_dir):
    """Create a sample configuration file."""
    config_path = os.path.join(temp_dir, "config.yaml")
    
    config = {
        "entity_registry": os.path.join(temp_dir, "entities.yaml"),
        "outputs": [
            {
                "type": "stdout",
                "name": "console"
            },
            {
                "type": "file",
                "name": "file_output",
                "file_path": os.path.join(temp_dir, "logs/test.log")
            }
        ],
        "time_patterns": [
            {
                "name": "business_hours",
                "base_frequency": 1.0,
                "start_time": "09:00",
                "end_time": "17:00",
                "days_of_week": ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY"],
                "multiplier": 2.0
            }
        ],
        "active_generators": ["test_generator"]
    }
    
    with open(config_path, "w") as f:
        yaml.dump(config, f)
        
    return config_path


@pytest.fixture
def sample_entities_file(temp_dir):
    """Create a sample entities file."""
    entities_path = os.path.join(temp_dir, "entities.yaml")
    
    entities = {
        "users": [
            {
                "username": "testuser",
                "full_name": "Test User",
                "email": "test@example.com",
                "department": "IT",
                "title": "Engineer",
                "is_admin": False
            }
        ],
        "devices": [
            {
                "hostname": "testhost",
                "ip_address": "192.168.1.100",
                "mac_address": "00:11:22:33:44:55",
                "os_type": "Windows",
                "os_version": "10"
            }
        ],
        "services": [
            {
                "name": "test-service",
                "port": 8080,
                "protocol": "HTTP",
                "description": "Test service"
            }
        ]
    }
    
    with open(entities_path, "w") as f:
        yaml.dump(entities, f)
        
    return entities_path


@pytest.fixture
def sample_template_file(temp_dir):
    """Create a sample template file."""
    templates_dir = os.path.join(temp_dir, "templates/vendor/product")
    os.makedirs(templates_dir, exist_ok=True)
    
    template_path = os.path.join(templates_dir, "sample.j2")
    with open(template_path, "w") as f:
        f.write("""
{
    "timestamp": "{{ timestamp }}",
    "hostname": "{{ hostname }}",
    "ip_address": "{{ ip_address }}",
    "username": "{{ username }}",
    "message": "This is a sample log entry",
    "event_id": {{ random_integer(1000, 9999) }},
    "sequence_num": {{ sequential_integer('seq') }},
    "guid": "{{ random_guid() }}"
}
        """)
    
    # Create metadata file
    metadata_path = os.path.join(templates_dir, "sample.meta.yaml")
    with open(metadata_path, "w") as f:
        yaml.dump({
            "vendor": "vendor",
            "product": "product",
            "data_source": "sample",
            "description": "Sample template for testing",
            "base_frequency": 1.0,
            "time_patterns": ["business_hours"],
            "is_generator": True
        }, f)
        
    return template_path