"""Test configuration for LogForge."""

import os
import pytest
import tempfile
import shutil


@pytest.fixture(scope="session")
def temp_dir():
    """Create a temporary directory for test files."""
    dir_path = tempfile.mkdtemp()
    yield dir_path
    shutil.rmtree(dir_path)