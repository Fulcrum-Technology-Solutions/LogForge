# LogForge Test Suite

This directory contains the test suite for the LogForge application.

## Overview

The test suite is organized as follows:

- `test_registry.py`: Tests for the entity registry functionality
- `test_templates.py`: Tests for the template rendering system
- `test_scheduler.py`: Tests for the time-based scheduling system
- `test_outputs.py`: Tests for the output adapters
- `test_engine.py`: Tests for the core engine
- `test_cli.py`: Tests for the command-line interface

## Running Tests

To run the tests, you'll need to install the development dependencies:

```bash
pip install -e ".[dev]"
```

Then, you can run the tests with pytest:

```bash
pytest
```

To run with coverage:

```bash
pytest --cov=logforge tests/
```

To generate a coverage report:

```bash
pytest --cov=logforge --cov-report=html tests/
```

## Test Configuration

The `conftest.py` file contains fixtures that are shared across tests, including:

- `temp_dir`: A temporary directory for test files
- `sample_config_file`: A sample configuration file
- `sample_entities_file`: A sample entities file
- `sample_template_file`: A sample template file

## Writing Tests

When writing new tests, follow these guidelines:

1. Use descriptive test names that explain what's being tested
2. Group tests into classes based on the component being tested
3. Use fixtures for common setup
4. Include docstrings that explain the purpose of each test
5. Test both normal and error cases

## CI/CD Integration

The tests are automatically run on GitHub Actions for each push and pull request. The workflow configuration is in `.github/workflows/tests.yml`.