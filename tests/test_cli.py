"""Tests for the CLI module."""

import os
import tempfile
import yaml
import pytest
from click.testing import CliRunner
from unittest.mock import patch, MagicMock

from synth_logs.cli import cli, load_config, setup_engine


class TestCLI:
    """Test the CLI commands."""
    
    def setup_method(self):
        """Set up test environment."""
        self.runner = CliRunner()
        
        # Create a temporary config file
        _, self.config_path = tempfile.mkstemp(suffix=".yaml")
        with open(self.config_path, 'w') as f:
            yaml.dump({
                'entity_registry': 'entities.yaml',
                'outputs': [],
                'active_generators': []
            }, f)
            
        # Create a temporary entities file
        _, self.entities_path = tempfile.mkstemp(suffix=".yaml")
        with open(self.entities_path, 'w') as f:
            yaml.dump({
                'users': [
                    {
                        'username': 'testuser',
                        'full_name': 'Test User',
                        'email': 'test@example.com'
                    }
                ],
                'devices': [],
                'services': []
            }, f)
        
    def teardown_method(self):
        """Clean up test environment."""
        os.unlink(self.config_path)
        os.unlink(self.entities_path)
        
    def test_load_config(self):
        """Test loading configuration from a file."""
        config = load_config(self.config_path)
        assert 'entity_registry' in config
        assert config['entity_registry'] == 'entities.yaml'
        
    def test_setup_engine(self):
        """Test setting up the engine from configuration."""
        config = {
            'entity_registry': self.entities_path,
            'outputs': [],
            'time_patterns': [
                {
                    'name': 'business_hours',
                    'base_frequency': 1.0,
                    'start_time': '09:00',
                    'end_time': '17:00',
                    'days_of_week': ['MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY'],
                    'multiplier': 2.0
                }
            ]
        }
        
        engine = setup_engine(config)
        assert engine is not None
        assert engine.registry is not None
        assert len(engine.scheduler.patterns) == 1
        
    @patch('synth_logs.cli.setup_engine')
    @patch('synth_logs.cli.click.echo')
    def test_run_command(self, mock_echo, mock_setup_engine):
        """Test the run command."""
        # Mock engine and its methods
        mock_engine = MagicMock()
        mock_setup_engine.return_value = mock_engine
        
        # Run the command
        result = self.runner.invoke(cli, ['run', '--config', self.config_path])
        
        # Command should have been interrupted by KeyboardInterrupt
        # which is mocked by the testing framework
        assert result.exit_code == 0
        mock_setup_engine.assert_called_once()
        mock_engine.discover_packages.assert_called_once()
        mock_engine.start.assert_called_once()
        
    @patch('synth_logs.cli.setup_engine')
    @patch('synth_logs.cli.click.echo')
    def test_run_command_with_entities(self, mock_echo, mock_setup_engine):
        """Test the run command with custom entities."""
        # Mock engine and its methods
        mock_engine = MagicMock()
        mock_setup_engine.return_value = mock_engine
        
        # Run the command with custom entities
        result = self.runner.invoke(cli, [
            'run', 
            '--config', self.config_path,
            '--entities', self.entities_path
        ])
        
        # Command should exit successfully
        assert result.exit_code == 0
        
        # Verify the entities path was overridden in the config
        args, kwargs = mock_setup_engine.call_args
        config = args[0]
        assert config['entity_registry'] == self.entities_path
        
    @patch('synth_logs.cli.setup_engine')
    @patch('synth_logs.cli.click.echo')
    def test_list_generators_command(self, mock_echo, mock_setup_engine):
        """Test the list_generators command."""
        # Mock engine and its methods
        mock_engine = MagicMock()
        mock_engine.generators = {
            'generator1': MagicMock(),
            'generator2': MagicMock()
        }
        mock_setup_engine.return_value = mock_engine
        
        # Run the command
        result = self.runner.invoke(cli, ['list-generators', '--config', self.config_path])
        
        # Command should exit successfully
        assert result.exit_code == 0
        mock_setup_engine.assert_called_once()
        mock_engine.discover_packages.assert_called_once()
        
        # Verify output includes both generators
        assert mock_echo.call_count >= 3  # At least header + 2 generators
        
    @pytest.mark.skipif(os.name != 'posix', reason="create-service only works on POSIX systems")
    def test_create_service_command(self):
        """Test the create-service command."""
        with tempfile.NamedTemporaryFile() as temp_file:
            # Run the command
            result = self.runner.invoke(cli, [
                'create-service',
                '--config', '/absolute/path/to/config.yaml',
                '--output', temp_file.name,
                '--description', 'Test Service'
            ])
            
            # Command should exit successfully
            assert result.exit_code == 0
            
            # Verify the service file was created
            content = temp_file.read().decode('utf-8')
            assert 'Description=Test Service' in content
            assert '--config /absolute/path/to/config.yaml' in content
            
    @pytest.mark.skipif(os.name != 'posix', reason="create-service only works on POSIX systems")
    def test_create_service_with_entities(self):
        """Test the create-service command with custom entities."""
        with tempfile.NamedTemporaryFile() as temp_file:
            # Run the command with custom entities
            result = self.runner.invoke(cli, [
                'create-service',
                '--config', '/absolute/path/to/config.yaml',
                '--entities', '/absolute/path/to/entities.yaml',
                '--output', temp_file.name
            ])
            
            # Command should exit successfully
            assert result.exit_code == 0
            
            # Verify the service file includes the entities path
            content = temp_file.read().decode('utf-8')
            assert '--config /absolute/path/to/config.yaml' in content
            assert '--entities /absolute/path/to/entities.yaml' in content