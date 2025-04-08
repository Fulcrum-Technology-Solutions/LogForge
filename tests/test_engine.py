"""Tests for the engine module."""

import tempfile
import os
import threading
import time
import pytest
from unittest.mock import MagicMock, patch

from synth_logs.core.engine import Engine, LogGenerator, TemplateBasedGenerator
from synth_logs.core.registry import EntityRegistry
from synth_logs.outputs.base import OutputAdapter


class MockGenerator(LogGenerator):
    """Mock implementation of LogGenerator for testing."""
    
    def __init__(self, name, frequency=1.0, mock_log="Test log entry"):
        super().__init__(name)
        self.frequency = frequency
        self.mock_log = mock_log
        self.generate_called = 0
        
    def generate(self, registry):
        """Generate a log entry."""
        self.generate_called += 1
        return self.mock_log
        
    def get_frequency(self):
        """Get the generation frequency."""
        return self.frequency


class MockOutput(OutputAdapter):
    """Mock implementation of OutputAdapter for testing."""
    
    def __init__(self, name):
        super().__init__(name)
        self.logs = []
        self.closed = False
        
    def send(self, log_entry):
        """Send a log entry."""
        self.logs.append(log_entry)
        return True
        
    def close(self):
        """Close the output."""
        self.closed = True


class TestLogGenerator:
    """Test the base LogGenerator class."""
    
    def test_initialization(self):
        """Test initializing a LogGenerator."""
        generator = MockGenerator("test_generator")
        assert generator.name == "test_generator"
        assert generator.active is False
        
    def test_generate_method(self):
        """Test the generate method."""
        generator = MockGenerator("test_generator")
        registry = EntityRegistry()
        
        log_entry = generator.generate(registry)
        assert log_entry == "Test log entry"
        assert generator.generate_called == 1
        
    def test_get_frequency_method(self):
        """Test the get_frequency method."""
        generator = MockGenerator("test_generator", frequency=2.5)
        assert generator.get_frequency() == 2.5


class TestTemplateBasedGenerator:
    """Test the TemplateBasedGenerator class."""
    
    def setup_method(self):
        """Set up test environment."""
        # Create a mock template manager
        self.template_manager = MagicMock()
        self.template_manager.render_template.return_value = "Rendered template"
        self.template_manager.random_private_ip.return_value = "192.168.1.1"
        
    def test_initialization(self):
        """Test initializing a TemplateBasedGenerator."""
        generator = TemplateBasedGenerator(
            name="test_generator",
            template_path="/path/to/template.j2",
            template_manager=self.template_manager,
            metadata={"base_frequency": 0.5}
        )
        
        assert generator.name == "test_generator"
        assert generator.template_path == "/path/to/template.j2"
        assert generator.template_manager == self.template_manager
        assert generator.base_frequency == 0.5
        
    def test_get_frequency(self):
        """Test the get_frequency method."""
        generator = TemplateBasedGenerator(
            name="test_generator",
            template_path="/path/to/template.j2",
            template_manager=self.template_manager,
            metadata={"base_frequency": 0.5}
        )
        
        # Basic frequency should match base_frequency
        frequency = generator.get_frequency()
        assert 0.4 <= frequency <= 0.6  # Account for randomness
        
    def test_generate(self):
        """Test the generate method."""
        generator = TemplateBasedGenerator(
            name="test_generator",
            template_path="/path/to/template.j2",
            template_manager=self.template_manager
        )
        
        registry = EntityRegistry()
        log_entry = generator.generate(registry)
        
        # Verify template manager was called correctly
        assert log_entry == "Rendered template"
        self.template_manager.render_template.assert_called_once()
        
    def test_generate_with_error(self):
        """Test the generate method when rendering fails."""
        self.template_manager.render_template.side_effect = Exception("Rendering error")
        
        generator = TemplateBasedGenerator(
            name="test_generator",
            template_path="/path/to/template.j2",
            template_manager=self.template_manager
        )
        
        registry = EntityRegistry()
        log_entry = generator.generate(registry)
        
        # Should return an error message
        assert "ERROR:" in log_entry


class TestEngine:
    """Test the Engine class."""
    
    def test_initialization(self):
        """Test initializing an Engine."""
        engine = Engine()
        assert engine.generators == {}
        assert engine.outputs == []
        assert isinstance(engine.registry, EntityRegistry)
        assert engine.running is False
        assert engine.threads == []
        
    def test_register_generator(self):
        """Test registering a generator."""
        engine = Engine()
        generator = MockGenerator("test_generator")
        
        engine.register_generator(generator)
        assert len(engine.generators) == 1
        assert engine.generators["test_generator"] == generator
        
    def test_add_output(self):
        """Test adding an output."""
        engine = Engine()
        output = MockOutput("test_output")
        
        engine.add_output(output)
        assert len(engine.outputs) == 1
        assert engine.outputs[0] == output
        
    def test_start_stop_generator(self):
        """Test starting and stopping a generator."""
        engine = Engine()
        generator = MockGenerator("test_generator")
        
        # Register the generator
        engine.register_generator(generator)
        
        # Initially not active
        assert generator.active is False
        
        # Start the generator
        with patch.object(threading, 'Thread') as mock_thread:
            mock_thread_instance = MagicMock()
            mock_thread.return_value = mock_thread_instance
            
            engine.start_generator("test_generator")
            
            assert generator.active is True
            mock_thread.assert_called_once()
            mock_thread_instance.start.assert_called_once()
            
        # Stop the generator
        engine.stop_generator("test_generator")
        assert generator.active is False
        
    def test_start_stop_engine(self):
        """Test starting and stopping the engine."""
        engine = Engine()
        generator1 = MockGenerator("generator1")
        generator2 = MockGenerator("generator2")
        
        # Register generators
        engine.register_generator(generator1)
        engine.register_generator(generator2)
        
        # Activate one generator
        generator1.active = True
        
        # Start the engine
        with patch.object(threading, 'Thread') as mock_thread:
            mock_thread_instance = MagicMock()
            mock_thread.return_value = mock_thread_instance
            
            engine.start()
            
            assert engine.running is True
            assert mock_thread.call_count == 1  # Only for the active generator
            
        # Stop the engine
        engine.stop()
        assert engine.running is False
        assert generator1.active is False
        assert generator2.active is False
        
    def test_generator_loop(self):
        """Test the generator loop functionality."""
        engine = Engine()
        output = MockOutput("test_output")
        generator = MockGenerator("test_generator", frequency=100.0)  # Fast generation
        
        # Add output and generator
        engine.add_output(output)
        engine.register_generator(generator)
        generator.active = True
        
        # Patch time.sleep to avoid actual waiting
        with patch('time.sleep'):
            # Set engine as running
            engine.running = True
            
            # Run the generator loop manually
            engine._generator_loop(generator)
            
            # Verify log was generated and sent to output
            assert generator.generate_called > 0
            assert len(output.logs) > 0
            assert output.logs[0] == "Test log entry"
            
    def test_send_to_outputs(self):
        """Test sending logs to multiple outputs."""
        engine = Engine()
        output1 = MockOutput("output1")
        output2 = MockOutput("output2")
        
        # Add outputs
        engine.add_output(output1)
        engine.add_output(output2)
        
        # Send a log entry
        engine._send_to_outputs("Test log entry")
        
        # Verify both outputs received the log
        assert len(output1.logs) == 1
        assert output1.logs[0] == "Test log entry"
        assert len(output2.logs) == 1
        assert output2.logs[0] == "Test log entry"
        
    @patch('importlib.metadata.entry_points')
    def test_discover_packages(self, mock_entry_points):
        """Test discovering packages via entry points."""
        # Mock entry points
        mock_entry_point = MagicMock()
        mock_entry_point.name = "test_package"
        mock_register_func = MagicMock()
        mock_entry_point.load.return_value = mock_register_func
        
        # Set up the mock to return our entry points
        mock_entry_points.return_value = MagicMock()
        mock_entry_points.return_value.__iter__.return_value = [mock_entry_point]
        
        # Also mock discover_generators to isolate this test
        engine = Engine()
        with patch.object(engine, 'discover_generators'):
            engine.discover_packages()
            
            # Verify the register function was called
            mock_register_func.assert_called_once_with(engine)
            
    @patch('os.path.splitext')
    def test_discover_template_generators(self, mock_splitext):
        """Test discovering template-based generators."""
        engine = Engine()
        
        # Mock the template manager
        engine.template_manager = MagicMock()
        
        # Set up template paths to discover
        template_paths = [
            "/templates/vendor1/product1/template1.j2",
            "/templates/vendor2/product2/template2.j2"
        ]
        engine.template_manager.get_all_template_paths.return_value = template_paths
        
        # Mock metadata
        mock_splitext.side_effect = lambda p: (p, ".j2")
        engine.template_manager.get_template_metadata.side_effect = lambda p: {
            "vendor": "vendor1" if "vendor1" in p else "vendor2",
            "product": "product1" if "product1" in p else "product2",
            "data_source": "logs",
            "is_generator": True
        }
        
        # Discover generators
        engine.discover_template_generators()
        
        # Verify generators were created
        assert "vendor1_product1_logs" in engine.generators
        assert "vendor2_product2_logs" in engine.generators
        assert len(engine.generators) == 2