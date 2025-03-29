# Prompt for Synthetic Event Log Generator Python Application

I need you to create a Python application for generating synthetic but realistic event logs from various products (Windows Event Log, Palo Alto Firewall, Palo Alto threat logs, Azure AD authentication). This is a detailed specification for the application.

## Core Requirements

1. Generate realistic logs in both format and volume/frequency
2. Define assets and identities that can be inserted into logs for realism and correlation
3. Use Jinja templates for log definition
4. Support multiple log formats including JSON, syslog, XML, and others
5. Support multiple outputs (stdout, flat file to local directory, HTTP)
6. Allow collaborators to easily add tech packages without modifying core code
7. Support multiple data sources per vendor (e.g., Palo Alto has firewall, threats, traffic, and system logs)
8. Run manually/headless, as a systemd service, or via a CLI menu
9. Allow users to add or remove log generators at runtime
10. Include profiles to control frequency and verbosity based on time patterns (e.g., more authentication logs in morning/evening)

## Architecture Overview

The application should use a plugin-based architecture with the following components:

1. **Core Engine**
   - Plugin management system using Python entry points
   - Entity registry for assets/identities
   - Time-based pattern scheduling
   - Output routing with adapter pattern

2. **Template System**
   - Jinja template engine integration
   - Helper functions for generating realistic values (GUIDs, IPs, port numbers, process IDs)
   - Integration with asset/identity registry

3. **Tech Packages**
   - Organized by vendor with submodules for different log types
   - Discoverable via Python entry points
   - Self-contained with their own templates and generation rules

4. **Runtime Interfaces**
   - Interactive CLI menu (using Click or Typer)
   - Headless operation
   - Systemd service support
   - Control API for runtime management

5. **Output Adapters**
   - STDOUT adapter
   - File system adapter
   - HTTP adapter
   - Error handling that allows stream to continue if output fails

## Detailed Component Specifications

### Core Engine

- Implement a plugin discovery system using Python entry points
- Create a registry system for assets and identities (users, devices, IPs, services)
- Design a scheduler that controls log generation frequency based on time patterns
- Implement an output routing system that directs logs to configured destinations

### Entity Registry

- Store information about users, devices, IP addresses, and services
- Provide methods for tech packages to access this information
- Allow importing predefined entities from external sources (CSV, JSON)
- Ensure consistent entity references across different log types

### Template System

- Use Jinja2 for template rendering
- Create helper functions/filters for:
  - Generating GUIDs
  - Creating realistic public/private IPs
  - Generating incrementing values (process IDs, port numbers)
  - Accessing entity registry information
  - Generating timestamps with proper formatting

### Tech Package Interface

- Define a clear interface for tech packages to implement
- Provide base classes that packages can extend
- Document the extension process for contributors
- Include example packages for common log sources

### Runtime Interfaces

- CLI menu using Click or Typer with color output
- Support for configuration files in YAML or JSON
- API endpoint for runtime management
- Proper signal handling for systemd integration

### Output Adapters

- Common interface for all output methods
- STDOUT adapter for console output
- File adapter with rotation support
- HTTP adapter with retry capability
- Exception handling that prevents output errors from stopping generation

## Example Tech Packages to Include

1. **Windows Event Log Package**
   - Security events
   - System events
   - Application events

2. **Palo Alto Package**
   - Firewall logs
   - Threat logs
   - Traffic logs
   - System logs

3. **Azure AD Package**
   - Authentication logs
   - Management events

## Example Code Structure

```
synth-logs/
├── synth_logs/
│   ├── __init__.py
│   ├── cli.py                 # CLI interface
│   ├── core/
│   │   ├── __init__.py
│   │   ├── engine.py          # Core engine
│   │   ├── registry.py        # Entity registry
│   │   ├── scheduler.py       # Time-based scheduler
│   │   └── templates.py       # Template utilities
│   ├── outputs/
│   │   ├── __init__.py
│   │   ├── base.py            # Output adapter interface
│   │   ├── stdout.py          # STDOUT adapter
│   │   ├── file.py            # File adapter
│   │   └── http.py            # HTTP adapter
│   ├── api/
│   │   ├── __init__.py
│   │   └── control.py         # Control API
│   └── utils/
│       ├── __init__.py
│       └── helpers.py         # Utility functions
├── packages/
│   ├── windows/
│   │   ├── __init__.py
│   │   ├── security.py
│   │   ├── system.py
│   │   └── application.py
│   ├── paloalto/
│   │   ├── __init__.py
│   │   ├── firewall.py
│   │   ├── threat.py
│   │   ├── traffic.py
│   │   └── system.py
│   └── azure/
│       ├── __init__.py
│       └── auth.py
├── templates/
│   ├── windows/
│   │   ├── security/
│   │   ├── system/
│   │   └── application/
│   ├── paloalto/
│   │   ├── firewall/
│   │   ├── threat/
│   │   ├── traffic/
│   │   └── system/
│   └── azure/
│       └── auth/
├── setup.py
├── README.md
└── config.yaml
```

## Implementation Notes

1. Use Python 3.8+ for compatibility with modern features
2. Implement proper error handling throughout
3. Add logging for the application itself
4. Include comprehensive docstrings
5. Create unit tests for core components
6. Focus on making extension as simple as possible for contributors
7. Implement streaming log generation to avoid memory issues
8. Make the frequency patterns flexible enough for realistic variation
9. Document the entity registry format clearly
10. Ensure all packages follow a consistent pattern

Please generate the code for this application, starting with the core modules and structure. Focus on creating a clean, well-documented, and extensible framework that meets all the requirements.