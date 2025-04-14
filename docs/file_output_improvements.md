# File Output Module Improvements

## Changes Implemented

The file output module in `logforge/outputs/file.py` has been streamlined and improved in the following ways:

### 1. Modern Path Handling

- Replaced string manipulation with Python's `pathlib` library
- Added more robust template path processing
- Simplified file key generation and tracking

### 2. Eliminated Complex Pattern Matching

- Removed hardcoded regex pattern checks for specific event types
- Prioritized metadata-based path construction instead of content parsing
- Simplified fallback logic to only parse JSON when necessary

### 3. Improved File Extension Determination

- Created a clear priority order for determining file extensions:
  1. Explicitly provided extension
  2. Format specified in metadata
  3. Extension from template path
  4. Default configured extension
- Unified handling of extensions with or without leading dots

### 4. Enhanced Data Source Extraction

- Prioritized metadata for data source identification
- Removed complex regex pattern matching for specific formats
- Simplified JSON extraction for data source fields

### 5. Added Configuration Options

- Added `use_template_structure` option to toggle template folder-based naming
- Added `custom_naming_pattern` option for future custom naming patterns
- Maintained backward compatibility with legacy configurations

### 6. Simplified File Management

- Restructured file tracking with a clearer dictionary format
- Improved file size tracking for rotation
- Reduced code duplication in file operations

### 7. Enhanced Documentation

- Added comprehensive docstrings to all methods
- Clarified parameter descriptions
- Added type hints for better code understanding

## Benefits

1. **More Dynamic:** The new implementation is more adaptable to various log formats
2. **Reduced Complexity:** Eliminated unnecessary regex pattern checks
3. **Improved Maintainability:** Cleaner code structure and better organization
4. **Better Testability:** Added unit tests for all key functionality

## Testing Approach

A comprehensive test suite has been added to validate all aspects of the streamlined module:

- File key generation tests
- Extension determination tests
- Data source extraction tests
- Folder structure extraction tests
- Filename sanitization tests
- File path generation tests

These tests ensure the module works correctly with various input combinations while maintaining backward compatibility with existing configurations.