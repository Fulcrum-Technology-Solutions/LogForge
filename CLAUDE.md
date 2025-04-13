# LogForge - Synthetic Event Log Generator (Claude Reference)

## Overview

LogForge is a Python application that generates realistic synthetic log data for security testing, development, and training. It supports multiple log formats (JSON, XML, syslog) from various systems (Windows, Palo Alto, Azure AD, etc.). The program uses templates and entity registries to create coherent, realistic logs with proper formatting and frequencies.

## Core Architecture

1. **Template-Based Generation**
   - Templates defined in Jinja2 format
   - Logs maintain their native format (XML, JSON, etc.)
   - Directory structure: `/templates/{vendor}/{product}/{data_source}/`

2. **Entity Registry**
   - Provides consistent entities (users, devices, services)
   - Ensures realistic relationships between entities
   - Defined in YAML format (`entities.yaml`)

3. **Output System**
   - Multiple output options (file, HTTP, stdout)
   - File output organization based on template paths
   - HTTP output with security and retry capability

4. **Scheduler**
   - Handles time-based patterns for realistic frequencies
   - Varies log generation rates based on time of day/week
   - Each generator has its own frequency profile

## Key Files and Directories

- `logforge/core/engine.py`: Central log generation engine
- `logforge/core/registry.py`: Entity registry management
- `logforge/core/templates.py`: Template handling
- `logforge/core/scheduler.py`: Time pattern scheduling
- `logforge/outputs/`: Output adapters (file, http, stdout)
- `templates/`: Log templates organized by vendor/product
- `config.yaml`: Main configuration file
- `entities.yaml`: Entity definitions

## Template System

Templates use Jinja2 with specialized functions:
- Random data generation (`random_guid()`, `random_ip()`)
- Entity access (`registry.get_random_user()`)
- Variable reuse with `set` statements for consistent entities

Example:
```jinja
{%- set user = registry.get_random_user() -%}
{%- set device = registry.get_random_device() -%}
```

## Latest Features

1. **Enhanced Device Entities (v1.2.0)**
   - Added FQDN field to devices
   - Extended device attributes (model, department, status, etc.)
   - Support for custom fields with `custom_` prefix
   - Improved Jinja2 access to all device fields in templates

2. **File Output Improvements (v1.1.0)**
   - Enhanced configuration with `output_dir`, `base_filename`, `default_extension`
   - File naming based on template folder structure
   - Intelligent extension handling

3. **Template Variable Reuse (v1.0.0)**
   - Consistent entity references using Jinja2 set statements
   - More coherent log entries with related fields
   - Improved template organization and readability

## Common Tasks

1. **Adding New Log Types**
   - Create template files in `/templates/{vendor}/{product}/{data_source}/`
   - Add corresponding `.meta.yaml` files with metadata
   - No code changes needed for most log types

2. **Configuring Outputs**
   - Edit `config.yaml` or use CLI configuration
   - File output uses folder structure for organization
   - HTTP output supports various authentication methods

3. **Controlling Log Frequency**
   - Define time patterns in config.yaml
   - Set base_frequency in template metadata
   - Use multipliers for different time periods

## Tests and Validation

- Test files located in `/tests/`
- Test file outputs in `/logforge/outputs/file.py` 
- Tests for registry in `/tests/test_registry.py`
- Template tests in `/tests/test_templates.py`

## Roadmap Considerations

1. **Event Relativity and Sequencing**
   - Add state tracking between events
   - Implement machine learning for logical sequences
   - Ensure consistent session IDs across related logs

2. **More Log Source Coverage**
   - Expand vendor/product coverage
   - Add more specialized security product logs
   - Support for cloud service logs

3. **Advanced Entity Features** ✓
   - ✓ Extended device attributes (model, department, status)
   - ✓ Support for organization-specific custom fields
   - ✓ Enhanced template access to all entity fields
   - Additional entity types (networks, applications)

4. **Template Improvements**
   - Variable inheritance between templates
   - Entity relationship enforcement
   - Dynamic template modification