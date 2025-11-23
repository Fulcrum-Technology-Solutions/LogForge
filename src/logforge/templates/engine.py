from __future__ import annotations

from typing import Any, Dict, List, Optional

from logforge.templates.loader import TemplateLoader
from logforge.templates.metadata import MetadataLoader, TemplateMetadata
from logforge.templates.renderer import TemplateRenderer


class TemplateEngine:
    def __init__(
        self,
        loader: TemplateLoader,
        metadata_loader: MetadataLoader,
        renderer: TemplateRenderer,
    ) -> None:
        self._loader = loader
        self._metadata_loader = metadata_loader
        self._renderer = renderer

    def render_event(self, template_id: str, context: Optional[Dict[str, Any]] = None) -> str:
        template_path = self._loader.resolve(template_id)
        return self._renderer.render(template_path, context)

    def get_metadata(self, template_id: str) -> TemplateMetadata:
        return self._metadata_loader.load_metadata(template_id)

    def list_templates(self) -> List[Dict[str, Any]]:
        entries = self._loader.list_templates()
        results: List[Dict[str, Any]] = []
        for template_id, locations in entries.items():
            info: Dict[str, Any] = {"id": template_id, "locations": list(locations.keys())}
            metadata = None
            for location, template_path in locations.items():
                metadata_path = template_path.with_name("metadata.yaml")
                try:
                    meta = self._metadata_loader.load_metadata_path(metadata_path)
                    if metadata is None:
                        metadata = meta
                except Exception:
                    continue
            if metadata:
                info["metadata"] = metadata.model_dump()
            results.append(info)
        return sorted(results, key=lambda item: item["id"])

    def get_template_detail(self, template_id: str) -> Dict[str, Any]:
        metadata = self.get_metadata(template_id)
        entries = self._loader.list_templates()
        locations = list(entries.get(template_id, {}).keys())
        return {
            "id": template_id,
            "metadata": metadata.model_dump(),
            "locations": locations,
        }

