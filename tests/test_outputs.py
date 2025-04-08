"""Tests for the output adapters."""

import os
import tempfile
import shutil
import pytest
from unittest.mock import patch, MagicMock
from synth_logs.outputs.base import OutputAdapter
from synth_logs.outputs.stdout import StdoutAdapter
from synth_logs.outputs.file import FileAdapter
from synth_logs.outputs.http import HttpAdapter


class TestOutputAdapter:
    """Test the base OutputAdapter class."""
    
    def test_initialization(self):
        """Test initializing an OutputAdapter."""
        # Create a concrete implementation of the abstract class
        class ConcreteAdapter(OutputAdapter):
            def send(self, log_entry):
                return True
            
            def close(self):
                pass
        
        adapter = ConcreteAdapter(name="test_adapter")
        assert adapter.name == "test_adapter"
        
    def test_abstract_methods(self):
        """Test that abstract methods raise NotImplementedError."""
        # Try to instantiate the abstract class
        with pytest.raises(TypeError):
            adapter = OutputAdapter(name="test_adapter")
            
        # Create a partial implementation
        class PartialAdapter(OutputAdapter):
            def send(self, log_entry):
                return True
                
        # Try to instantiate without implementing all abstract methods
        with pytest.raises(TypeError):
            adapter = PartialAdapter(name="test_adapter")


class TestStdoutAdapter:
    """Test the StdoutAdapter class."""
    
    def test_initialization(self):
        """Test initializing a StdoutAdapter."""
        adapter = StdoutAdapter(name="stdout_test")
        assert adapter.name == "stdout_test"
        
    def test_send(self, capsys):
        """Test sending a log entry to stdout."""
        adapter = StdoutAdapter(name="stdout_test")
        
        # Send a test message
        adapter.send("Test log entry")
        
        # Capture the output
        captured = capsys.readouterr()
        assert "Test log entry" in captured.out
        
    def test_send_with_extension(self, capsys):
        """Test sending a log entry with extension info."""
        adapter = StdoutAdapter(name="stdout_test")
        
        # Send a test message with extension
        adapter.send_with_extension("Test log entry", ".json", {"vendor": "test"})
        
        # Capture the output
        captured = capsys.readouterr()
        assert "Test log entry" in captured.out
        
    def test_close(self):
        """Test closing the adapter."""
        adapter = StdoutAdapter(name="stdout_test")
        # Close should not raise any exceptions
        adapter.close()


class TestFileAdapter:
    """Test the FileAdapter class."""
    
    def setup_method(self):
        """Set up a temporary directory for file testing."""
        self.temp_dir = tempfile.mkdtemp()
        
    def teardown_method(self):
        """Clean up the temporary directory."""
        shutil.rmtree(self.temp_dir)
        
    def test_initialization(self):
        """Test initializing a FileAdapter."""
        file_path = os.path.join(self.temp_dir, "test.log")
        adapter = FileAdapter(
            name="file_test",
            file_path=file_path,
            max_size=1024,
            backup_count=3,
            hourly_rotation=True
        )
        
        assert adapter.name == "file_test"
        assert adapter.file_path == file_path
        assert adapter.max_size == 1024
        assert adapter.backup_count == 3
        assert adapter.hourly_rotation is True
        
    def test_send(self):
        """Test sending a log entry to a file."""
        file_path = os.path.join(self.temp_dir, "test.log")
        adapter = FileAdapter(
            name="file_test",
            file_path=file_path
        )
        
        # Send a test message
        result = adapter.send("Test log entry")
        assert result is True
        
        # Verify the file was created with the correct content
        with open(file_path, "r") as f:
            content = f.read()
            assert "Test log entry" in content
            
    def test_send_with_extension(self):
        """Test sending a log entry with extension info."""
        file_path = os.path.join(self.temp_dir, "test.log")
        adapter = FileAdapter(
            name="file_test",
            file_path=file_path,
            data_source_field="generator"
        )
        
        # Send a test message with extension
        metadata = {"generator": "test_generator"}
        result = adapter.send_with_extension("Test log entry", ".json", metadata)
        assert result is True
        
        # Verify the file was created
        # For data_source segmentation, it would create a subfolder based on the generator
        expected_path = os.path.join(self.temp_dir, "test_generator", "test.log")
        assert os.path.exists(file_path) or os.path.exists(expected_path)
        
    def test_close(self):
        """Test closing the adapter."""
        file_path = os.path.join(self.temp_dir, "test.log")
        adapter = FileAdapter(
            name="file_test",
            file_path=file_path
        )
        
        # Send a message to create the file
        adapter.send("Test log entry")
        
        # Close the adapter
        adapter.close()
        
        # Verify the file still exists (close shouldn't delete it)
        assert os.path.exists(file_path)


class TestHttpAdapter:
    """Test the HttpAdapter class."""
    
    def test_initialization(self):
        """Test initializing an HttpAdapter."""
        adapter = HttpAdapter(
            name="http_test",
            url="http://example.com/logs",
            method="POST",
            headers={"Content-Type": "application/json"},
            retry_count=3,
            retry_delay=1.0,
            timeout=5.0,
            verify_ssl=True
        )
        
        assert adapter.name == "http_test"
        assert adapter.url == "http://example.com/logs"
        assert adapter.method == "POST"
        assert adapter.headers == {"Content-Type": "application/json"}
        assert adapter.retry_count == 3
        assert adapter.retry_delay == 1.0
        assert adapter.timeout == 5.0
        assert adapter.verify_ssl is True
        
    @patch("requests.request")
    def test_send_success(self, mock_request):
        """Test sending a log entry successfully via HTTP."""
        # Configure the mock to return a success response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.ok = True
        mock_request.return_value = mock_response
        
        adapter = HttpAdapter(
            name="http_test",
            url="http://example.com/logs"
        )
        
        # Send a test message
        result = adapter.send("Test log entry")
        
        # Verify the request was made correctly
        assert result is True
        mock_request.assert_called_once()
        args, kwargs = mock_request.call_args
        assert kwargs["url"] == "http://example.com/logs"
        assert kwargs["method"] == "POST"
        assert kwargs["data"] == "Test log entry"
        
    @patch("requests.request")
    def test_send_failure(self, mock_request):
        """Test sending a log entry with HTTP failure."""
        # Configure the mock to return a failure response
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.ok = False
        mock_request.return_value = mock_response
        
        adapter = HttpAdapter(
            name="http_test",
            url="http://example.com/logs",
            retry_count=2
        )
        
        # Send a test message
        result = adapter.send("Test log entry")
        
        # Verify the request was made and retried
        assert result is False
        assert mock_request.call_count == 3  # Initial + 2 retries
        
    @patch("requests.request")
    def test_send_with_extension(self, mock_request):
        """Test sending a log entry with extension info via HTTP."""
        # Configure the mock to return a success response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.ok = True
        mock_request.return_value = mock_response
        
        adapter = HttpAdapter(
            name="http_test",
            url="http://example.com/logs"
        )
        
        # Send a test message with extension
        metadata = {"vendor": "test", "product": "product"}
        result = adapter.send_with_extension("Test log entry", ".json", metadata)
        
        # Verify the request was made correctly
        assert result is True
        mock_request.assert_called_once()
        
    def test_close(self):
        """Test closing the adapter."""
        adapter = HttpAdapter(
            name="http_test",
            url="http://example.com/logs"
        )
        
        # Close should not raise any exceptions
        adapter.close()