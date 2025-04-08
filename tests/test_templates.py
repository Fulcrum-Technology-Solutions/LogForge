"""Tests for the templates module."""

import os
import tempfile
import pytest
from synth_logs.core.templates import TemplateManager
from synth_logs.core.registry import EntityRegistry


class TestTemplateManager:
    """Test the TemplateManager class."""
    
    def test_initialization(self):
        """Test initializing a TemplateManager."""
        manager = TemplateManager()
        assert manager.template_dirs is not None
        assert manager.env is not None
        
    def test_initialization_with_dirs(self):
        """Test initializing a TemplateManager with custom template directories."""
        test_dirs = ["/tmp/test1", "/tmp/test2"]
        manager = TemplateManager(test_dirs)
        assert manager.template_dirs == test_dirs
        
    def test_random_guid(self):
        """Test the random_guid filter."""
        manager = TemplateManager()
        guid = manager.random_guid()
        
        # Check that the GUID has the correct format
        assert len(guid) == 36
        assert guid.count("-") == 4
        
    def test_random_ip(self):
        """Test the random_ip filter."""
        manager = TemplateManager()
        ip = manager.random_ip()
        
        # Check that the IP has the correct format
        parts = ip.split(".")
        assert len(parts) == 4
        for part in parts:
            assert 0 <= int(part) <= 255
            
    def test_random_private_ip(self):
        """Test the random_private_ip filter."""
        manager = TemplateManager()
        ip = manager.random_private_ip()
        
        # Check that the IP is in a private range
        parts = ip.split(".")
        assert len(parts) == 4
        
        first_octet = int(parts[0])
        second_octet = int(parts[1])
        
        is_private = (
            first_octet == 10 or
            (first_octet == 172 and 16 <= second_octet <= 31) or
            (first_octet == 192 and second_octet == 168)
        )
        
        assert is_private is True
        
    def test_random_integer(self):
        """Test the random_integer filter."""
        manager = TemplateManager()
        
        # Test with defaults
        num = manager.random_integer()
        assert isinstance(num, int)
        assert 0 <= num <= 1000
        
        # Test with custom range
        num = manager.random_integer(min_val=100, max_val=200)
        assert isinstance(num, int)
        assert 100 <= num <= 200
        
    def test_sequential_integer(self):
        """Test the sequential_integer filter."""
        manager = TemplateManager()
        
        # Get several sequential integers and verify they increment
        prev = manager.sequential_integer("test")
        assert isinstance(prev, int)
        
        for _ in range(5):
            current = manager.sequential_integer("test")
            assert current == prev + 1
            prev = current
            
        # Test with a different sequence name
        assert manager.sequential_integer("other") != prev
        
        # Test with starting value
        seq = manager.sequential_integer("new_seq", start=1000)
        assert seq == 1000
        assert manager.sequential_integer("new_seq") == 1001
        
    def test_render_template_string(self):
        """Test rendering a template string."""
        manager = TemplateManager()
        registry = EntityRegistry()
        
        # Simple template
        result = manager.render_template_string(
            "Hello, {{ name }}!",
            registry,
            {"name": "World"}
        )
        assert result == "Hello, World!"
        
        # Template with filters
        result = manager.render_template_string(
            "Random number: {{ random_integer(10, 10) }}",
            registry,
            {}
        )
        assert result == "Random number: 10"
        
    def test_get_template_metadata(self):
        """Test getting metadata for a template."""
        # Create a temporary template file with metadata
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a template file
            template_path = os.path.join(temp_dir, "test.j2")
            with open(template_path, "w") as f:
                f.write("Test template")
                
            # Create a metadata file
            meta_path = os.path.join(temp_dir, "test.meta.yaml")
            with open(meta_path, "w") as f:
                f.write("""
vendor: Test
product: Product
data_source: Logs
description: Test template
base_frequency: 1.0
                """)
                
            # Initialize the template manager with the temp directory
            manager = TemplateManager([temp_dir])
            
            # Get the metadata
            metadata = manager.get_template_metadata(template_path)
            
            # Verify the metadata
            assert metadata is not None
            assert metadata["vendor"] == "Test"
            assert metadata["product"] == "Product"
            assert metadata["data_source"] == "Logs"
            assert metadata["description"] == "Test template"
            assert metadata["base_frequency"] == 1.0