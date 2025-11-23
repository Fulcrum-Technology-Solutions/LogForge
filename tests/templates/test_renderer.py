from __future__ import annotations

from pathlib import Path

from logforge.entities.functions import RegistryFunctions
from logforge.templates.renderer import TemplateRenderer


class SimpleModel:
    def __init__(self, **data):
        self._data = data

    def dict(self):
        return self._data


class StubRegistry:
    def get_random_user(self):
        return SimpleModel(username="alice")

    def get_random_device(self):
        return SimpleModel(hostname="device01")

    def get_random_service(self):
        return SimpleModel(name="svc")

    def get_user(self, username: str):
        return SimpleModel(username=username)

    def get_device(self, hostname: str):
        return SimpleModel(hostname=hostname)

    def get_service(self, name: str):
        return SimpleModel(name=name)

    def get_organization(self):
        return SimpleModel(domain="example.com")

    def get_organization_field(self, key: str):
        return "example.com" if key == "domain" else None

    def get_organization_contact(self, key: str):
        return "admin@example.com" if key == "admin" else None


def test_renderer_injects_registry_and_fake(tmp_path):
    template_root = tmp_path / "templates"
    template_root.mkdir()
    template_path = template_root / "sample.j2"
    template_path.write_text(
        "{{ registry.get_organization()['domain'] }}|{{ registry.get_random_user().username }}|{{ fake.name() }}",
        encoding="utf-8",
    )

    renderer = TemplateRenderer(template_root, RegistryFunctions(StubRegistry()))  # type: ignore[arg-type]
    output = renderer.render(template_path.relative_to(template_root))

    assert output.startswith("example.com|alice|")


def test_renderer_accepts_absolute_paths(tmp_path):
    template_root = tmp_path / "templates"
    template_root.mkdir()
    template_path = template_root / "sample.j2"
    template_path.write_text("{{ random_int(1, 1) }}", encoding="utf-8")

    renderer = TemplateRenderer(template_root)
    output = renderer.render(template_path)

    assert output.strip() == "1"

