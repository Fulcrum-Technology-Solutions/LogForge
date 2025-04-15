# Template Verification Guide

LogForge includes tools to verify and fix common issues in Jinja2 templates, ensuring they follow best practices and produce correct output.

## Common Template Issues

### 1. Whitespace Control Issues

When using Jinja2 set statements without whitespace control, the output can contain unwanted empty lines:

```jinja
{% set username = "user" %}
{% set timestamp = current_timestamp() %}
{
  "username": "{{ username }}",
  "timestamp": "{{ timestamp }}"
}
```

This produces output with unwanted newlines:

```json

{
  "username": "user",
  "timestamp": "2021-01-01T00:00:00Z"
}
```

### 2. Proper Whitespace Control

The correct approach uses whitespace control markers (`{%-` and `-%}`):

```jinja
{%- set username = "user" -%}
{%- set timestamp = current_timestamp() -%}
{
  "username": "{{ username }}",
  "timestamp": "{{ timestamp }}"
}
```

This produces clean output:

```json
{
  "username": "user",
  "timestamp": "2021-01-01T00:00:00Z"
}
```

## Automated Tests

LogForge includes automated tests to verify template quality:

- `test_template_syntax_validity`: Checks that all templates have valid Jinja2 syntax
- `test_template_whitespace_control`: Identifies templates with missing whitespace control
- `test_metadata_validity`: Ensures all templates have complete metadata files
- `test_template_rendering`: Verifies that all templates render correctly

Run the tests with:

```bash
pytest tests/test_template_verification.py -v
```

## Template Fixer Tool

LogForge provides a utility to automatically fix common template issues:

```bash
# Check for issues without making changes
python -m logforge.utils.template_fixer --dir templates --fix-whitespace --dry-run

# Fix whitespace control issues
python -m logforge.utils.template_fixer --dir templates --fix-whitespace

# Check metadata files for issues
python -m logforge.utils.template_fixer --dir templates --check-metadata
```

## Best Practices

1. **Always use whitespace control** for set statements:
   ```jinja
   {%- set variable = value -%}
   ```

2. **Ensure each template has a metadata file** with:
   - `vendor`, `product`, `data_source`, and `format` fields
   - Appropriate generator settings

3. **Document context requirements** in metadata's `context` section

4. **Validate rendered output** matches the declared format

Following these best practices will ensure your templates work correctly and produce well-formed output.