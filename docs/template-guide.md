# Template Development Guide

LogForge templates are Jinja2 documents paired with metadata that describe how events
should be rendered. Templates live under your templates directory
(`~/.logforge/templates` by default) and can be pulled from the community API,
customized locally, or authored from scratch.

## Directory Structure

Each template resides in a directory mirroring its template ID:

```
templates/
└── custom/
    └── vendor/product/example/
        ├── metadata.yaml
        └── template.j2
```

* `metadata.yaml` – declarative information about the template (id, version,
  vendor, tags, etc.).
* `template.j2` – the Jinja2 template that renders a single event payload.

Template IDs map directly to directory paths. An ID such as
`examples/windows_eventlog/security` becomes
`templates/custom/examples/windows_eventlog/security`.

## Metadata Reference

The metadata file accepts the fields defined in `TemplateMetadata`. The most
commonly used keys are:

| Key           | Required | Description                                  |
|---------------|----------|----------------------------------------------|
| `id`          | ✅        | Unique identifier used in generator config.  |
| `name`        | ✅        | Human friendly name.                         |
| `description` |          | Short description for documentation/UI.      |
| `vendor`      |          | Vendor/author of the data source.            |
| `product`     |          | Product family (e.g., Windows, Palo Alto).   |
| `version`     |          | Template version string.                     |
| `format`      |          | Output format (`json`, `text`, etc.).        |
| `tags`        |          | List of keywords.                            |
| `variables`   |          | Variable metadata for UIs/documentation.     |

Example (`metadata.yaml`):

```yaml
id: examples/windows_eventlog/security
name: Windows Security Event
description: Synthetic Windows Event Log security message
vendor: Microsoft
product: Windows
version: "1.0.0"
format: json
tags:
  - windows
  - security
  - eventlog
```

## Rendering Helpers

Templates are rendered with a Jinja2 environment that exposes helper functions:

| Helper               | Description                                                |
|----------------------|------------------------------------------------------------|
| `now()`              | Returns current UTC timestamp (`datetime`).                |
| `random_int(a, b)`   | Inclusive random integer between `a` and `b`.              |
| `random_choice(seq)` | Random element from the provided list/sequence.            |
| `fake`               | Instance of [`faker.Faker`](https://faker.readthedocs.io/) |
| `registry`           | Access to `RegistryFunctions` for entity lookups.          |

The `registry` helper surfaces:

- `registry.get_random_user()`
- `registry.get_random_device()`
- `registry.get_random_service()`
- `registry.get_organization()`

Use these helpers to populate generated events with realistic values:

```jinja
{
  "event_id": {{ random_int(4624, 4625) }},
  "service": "{{ random_choice(['billing', 'orders', 'identity']) }}",
  "user": "{{ registry.get_random_user().username if registry.get_random_user() else 'anonymous' }}",
  "request_id": "{{ fake.uuid4() }}",
  "timestamp": "{{ now().isoformat() }}"
}
```

## Creating a New Template

1. Decide on a template ID, e.g. `custom/web/checkout`.
2. Create the directory structure under `templates/custom/`.
3. Author `metadata.yaml` with the required fields.
4. Write `template.j2`, leveraging helpers and Jinja2 syntax.
5. Validate locally:
   ```bash
   logforge templates validate --template-id custom/web/checkout
   ```
6. Reference the template ID from a generator definition.

## Customising Existing Templates

```bash
logforge templates customize examples/windows_eventlog/security
```

The command copies the template into the `custom` directory. Modify
`template.j2` or `metadata.yaml` as needed and rerun validation.

To view differences:

```bash
logforge templates diff examples/windows_eventlog/security
```

To revert to the default version:

```bash
logforge templates revert examples/windows_eventlog/security
```

## Community Templates

Search and install templates published to the community API:

```bash
logforge templates search ransomware
logforge templates install community/windows/ransomware_v1
```

Installed templates are stored under the default directory and can be
customized like any other template.

## Best Practices

- Keep metadata concise but descriptive for operators and UI surfaces.
- Use entity registry helpers to ensure generated events reference valid users,
  devices, and services.
- Prefer UTC timestamps (`now()`) and include contextual metadata (e.g., source
  IP, request identifiers).
- Validate templates regularly as part of your CI workflow.
- Store example payloads in tests to guard against template regressions.

With these patterns you can build a curated catalog of synthetic log sources
that mirror production telemetry while remaining entirely safe to share.

