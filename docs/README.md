# Logforge Documentation

This directory contains documentation and examples for extending and using Logforge.

## Contents

- `generator_template/`: A template for creating custom log generators
  - Contains a complete example generator implementation
  - Shows how to use the entry points system to register generators
  - Demonstrates best practices for template organization and metadata

## Creating Custom Generators

Logforge uses Python's entry points system to discover and load generators at runtime. This allows you to create and distribute custom generators without modifying the core codebase.

See the `generator_template/` directory for a complete example.

## Template System

Logforge uses Jinja2 templates to define the format of log entries. Each template has an associated metadata file that provides information about the template, including:

- Vendor and product names
- Data source description
- Format information
- Required parameters

See `generator_template/README.md` for detailed information on how to create and use templates.