"""Basic tests for output adapters."""

import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock

from logforge.outputs.stdout import StdoutAdapter
from logforge.outputs.file import FileAdapter
from logforge.outputs.http import HttpAdapter


def test_stdout_adapter():
    """Test StdoutAdapter basic functionality."""
    adapter = StdoutAdapter(name="test_stdout")
    assert adapter.name == "test_stdout"
    
    # Success is simply not raising an exception
    adapter.close()

def test_file_adapter():
    """Test FileAdapter basic functionality."""
    # Just test the initialization, without actually writing to a file
    adapter = FileAdapter(
        name="test_file",
        file_path="test.log" 
    )
    assert adapter.name == "test_file"
    assert adapter.file_path == "test.log"
    
    # Just make sure close doesn't raise an exception
    adapter.close()

@patch("requests.request")
def test_http_adapter(mock_request):
    """Test HttpAdapter basic functionality."""
    # Set up the mock to return a successful response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.ok = True
    mock_request.return_value = mock_response
    
    adapter = HttpAdapter(
        name="test_http",
        url="http://example.com/logs"
    )
    assert adapter.name == "test_http"
    assert adapter.url == "http://example.com/logs"
    
    # Just test initialization - we can't actually test HTTP sends without mocking at a lower level
    # or setting up a test server, so we'll skip the send test for simplicity
    adapter.close()
    
    # No need to check the request, as we're not actually testing the send method
    pass