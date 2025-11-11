from __future__ import annotations

import difflib
from pathlib import Path
from typing import Any, Dict, List, Optional

from logforge.community.client import CommunityAPIClient
from logforge.core.config import LogForgeConfig
from logforge.entities.functions import RegistryFunctions
from logforge.entities.registry import EntityRegistry
from logforge.templates.loader import TemplateLoader
from logforge.templates.renderer import TemplateRenderer
from logforge.templates.validator import TemplateValidationError, TemplateValidator


class TemplateManager:
    def __init__(self, config: LogForgeConfig, registry: EntityRegistry) -> None:
        self.config = config
        self.loader = TemplateLoader(config.templates)
        self.registry_functions = RegistryFunctions(registry)
        self.renderer = TemplateRenderer(self.loader, self.registry_functions)
        self.validator = TemplateValidator(self.loader, self.registry_functions)
        self.community = CommunityAPIClient(config.templates.community_api_url)

    def list_templates(self) -> List[Dict]:
        templates = []
        for record in self.loader.list_templates():
            templates.append(
                {
                    "id": record.id,
                    "name": record.name,
                    "version": record.version,
                    "location": record.location,
                    "overrides": record.overrides,
                }
            )
        return templates

    def template_info(self, template_id: str) -> Dict:
        record = self.loader.get_template(template_id)
        return {
            "id": record.id,
            "name": record.name,
            "version": record.version,
            "location": record.location,
            "metadata": record.metadata.model_dump(),
            "overrides": record.overrides,
        }

    def validate(self, template_id: str) -> Dict:
        metadata = self.validator.validate_template(template_id)
        return metadata.model_dump()

    def validate_path(self, path: Path) -> Dict:
        metadata = self.validator.validate_path(path)
        return metadata.model_dump()

    def render(self, template_id: str, extra_context: Optional[Dict] = None) -> str:
        return self.renderer.render(template_id, extra_context=extra_context or {})

    def install_from_remote(self, template_id: str) -> Dict:
        payload = self.community.download_template(template_id)
        target = self.loader.paths.default_dir / Path(template_id)
        target.mkdir(parents=True, exist_ok=True)
        for relative, content in payload["files"].items():
            path = target / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        return self.template_info(template_id)

    def search_remote(self, query: Optional[str] = None, vendor: Optional[str] = None) -> List[Dict[str, Any]]:
        return self.community.list_templates(query=query, vendor=vendor)

    def customize(self, template_id: str) -> Path:
        return self.loader.customize(template_id)

    def diff(self, template_id: str) -> str:
        custom = self.loader.get_template(template_id)
        if custom.location != "custom":
            raise TemplateValidationError("No custom template to diff.")
        default_path = self.loader._template_path(self.loader.paths.default_dir, template_id)
        if not default_path:
            raise TemplateValidationError("No default template to diff against.")
        custom_source = (custom.path / "template.j2").read_text(encoding="utf-8").splitlines()
        default_source = (default_path / "template.j2").read_text(encoding="utf-8").splitlines()
        diff = difflib.unified_diff(default_source, custom_source, fromfile="default", tofile="custom", lineterm="")
        return "\n".join(diff)

    def revert(self, template_id: str) -> None:
        self.loader.revert(template_id)
