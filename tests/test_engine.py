"""Basic tests for the engine module."""

import pytest
from unittest.mock import MagicMock, patch

from logforge.core.engine import Engine, LogGenerator, TemplateBasedGenerator
from logforge.core.registry import EntityRegistry, User, Device
from logforge.outputs.base import OutputAdapter


class MockGenerator(LogGenerator):
    """Mock generator for testing."""
    def __init__(self, name):
        super().__init__(name)
        self.generate_count = 0
        
    def generate(self, registry):
        self.generate_count += 1
        return f"Test log from {self.name}"
        
    def get_frequency(self):
        return 1.0


class MockOutput(OutputAdapter):
    """Mock output adapter for testing."""
    def __init__(self, name):
        super().__init__(name)
        self.logs = []
        
    def send(self, log_entry):
        self.logs.append(log_entry)
        return True
        
    def close(self):
        pass


def test_engine_init():
    """Test Engine initialization."""
    engine = Engine()
    assert engine.generators == {}
    assert engine.outputs == []
    assert isinstance(engine.registry, EntityRegistry)
    assert engine.running is False

def test_register_generator():
    """Test registering a generator."""
    engine = Engine()
    generator = MockGenerator("test_generator")
    
    engine.register_generator(generator)
    assert len(engine.generators) == 1
    assert engine.generators["test_generator"] == generator

def test_add_output():
    """Test adding an output."""
    engine = Engine()
    output = MockOutput("test_output")
    
    engine.add_output(output)
    assert len(engine.outputs) == 1
    assert engine.outputs[0] == output

def test_send_to_outputs():
    """Test sending to outputs."""
    engine = Engine()
    output1 = MockOutput("output1")
    output2 = MockOutput("output2")
    
    engine.add_output(output1)
    engine.add_output(output2)
    
    engine._send_to_outputs("Test log entry")
    
    assert len(output1.logs) == 1
    assert output1.logs[0] == "Test log entry"
    assert len(output2.logs) == 1
    assert output2.logs[0] == "Test log entry"