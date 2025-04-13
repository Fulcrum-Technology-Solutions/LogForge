"""Tests for CLI functionality."""

import os
import tempfile
import pytest
import yaml
import re
from unittest.mock import patch, MagicMock
from click.testing import CliRunner

from logforge.cli import cli, load_config
from logforge import __version__


@pytest.fixture
def config_file():
    """Create a temporary config file."""
    temp_file_path = os.path.join(tempfile.gettempdir(), "test_config.yaml")
    config = {
        'entity_registry': 'entities.yaml',
        'outputs': [
            {
                'type': 'file',
                'name': 'test_output',
                'file_path': 'test.log'
            }
        ],
        'active_generators': []
    }
    with open(temp_file_path, 'w') as temp_file:
        yaml.dump(config, temp_file)
    
    yield temp_file_path
    
    # Clean up
    os.unlink(temp_file_path)


def test_load_config(config_file):
    """Test loading configuration."""
    config = load_config(config_file)
    assert 'entity_registry' in config
    assert config['entity_registry'] == 'entities.yaml'
    assert 'outputs' in config
    assert len(config['outputs']) == 1


@patch('logforge.cli.setup_engine')
@patch('logforge.cli.click.echo')
def test_list_generators(mock_echo, mock_setup_engine, config_file):
    """Test list_generators command."""
    # Mock engine
    mock_engine = MagicMock()
    mock_engine.generators = {
        'generator1': MagicMock(),
        'generator2': MagicMock()
    }
    mock_setup_engine.return_value = mock_engine
    
    # Run command
    runner = CliRunner()
    result = runner.invoke(cli, ['list-generators', '--config', config_file])
    
    # Verify command ran successfully
    assert result.exit_code == 0
    mock_setup_engine.assert_called_once()
    mock_engine.discover_packages.assert_called_once()
    
    # Verify output includes generators
    assert mock_echo.called
    
def test_version_flag():
    """Test the --version flag."""
    runner = CliRunner()
    result = runner.invoke(cli, ['--version'])
    
    assert result.exit_code == 0
    assert re.search(f"version {__version__}", result.output)