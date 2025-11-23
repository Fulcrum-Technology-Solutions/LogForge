from __future__ import annotations

import difflib
import io
import shutil
import zipfile
from pathlib import Path
from typing import Dict, List, Optional

from logforge.core.config import TemplateConfig, resolve_logforge_home
from logforge.templates.loader import TemplateLoader
from logforge.templates.metadata import MetadataLoader


class TemplateManager:
    def __init__(
        self,
        config: TemplateConfig,
        loader: TemplateLoader,
        metadata_loader: MetadataLoader,
    ) -> None:
        self._config = config
        self._loader = loader
        self._metadata_loader = metadata_loader
        home = resolve_logforge_home()
        self._local_path = self._resolve_path(home, config.local_path)
        self._default_path = self._resolve_path(home, config.default_path)
        self._custom_path = self._resolve_path(home, config.custom_path)

    def search(self, query: Optional[str] = None) -> List[Dict[str, any]]:
        results = []
        for template_id, location_map in self._loader.list_templates().items():
            if query and query.lower() not in template_id.lower():
                continue
            metadata_dict: Dict[str, any] = {}
            template_path = next(iter(location_map.values()), None)
            if template_path:
                metadata_path = Path(template_path).with_name("metadata.yaml")
                if metadata_path.exists():
                    try:
                        metadata = self._metadata_loader.load_metadata_path(metadata_path)
                        metadata_dict = metadata.model_dump()
                    except Exception:
                        metadata_dict = {}
            results.append(
                {
                    "id": template_id,
                    "locations": list(location_map.keys()),
                    "name": metadata_dict.get("name"),
                    "vendor": metadata_dict.get("vendor"),
                    "product": metadata_dict.get("product"),
                    "data_source": metadata_dict.get("data_source"),
                    "version": metadata_dict.get("version"),
                    "format": metadata_dict.get("format"),
                }
            )
        return sorted(results, key=lambda item: item["id"])

    def install_package(self, package_bytes: bytes) -> None:
        with zipfile.ZipFile(io.BytesIO(package_bytes)) as archive:
            archive.extractall(self._default_path)

    def customize(self, template_id: str) -> Path:
        default_dir = self._resolve_template_dir(template_id, self._default_path)
        if not default_dir.exists():
            raise FileNotFoundError(f"Default template not found for {template_id}")
        custom_dir = self._resolve_template_dir(template_id, self._custom_path)
        if custom_dir.exists():
            raise FileExistsError(f"Custom template already exists for {template_id}")
        custom_dir.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(default_dir, custom_dir)
        return custom_dir

    def revert(self, template_id: str) -> None:
        custom_dir = self._resolve_template_dir(template_id, self._custom_path)
        if not custom_dir.exists():
            raise FileNotFoundError(f"Custom template not found for {template_id}")
        shutil.rmtree(custom_dir)

    def diff(self, template_id: str) -> str:
        default_dir = self._resolve_template_dir(template_id, self._default_path)
        custom_dir = self._resolve_template_dir(template_id, self._custom_path)
        if not custom_dir.exists():
            raise FileNotFoundError(f"Custom template not found for {template_id}")
        default_template = (default_dir / "template.j2").read_text(encoding="utf-8")
        custom_template = (custom_dir / "template.j2").read_text(encoding="utf-8")
        diff_lines = difflib.unified_diff(
            default_template.splitlines(),
            custom_template.splitlines(),
            fromfile="default/template.j2",
            tofile="custom/template.j2",
            lineterm="",
        )
        return "\n".join(diff_lines)

    def merge(self, template_id: str) -> None:
        default_dir = self._resolve_template_dir(template_id, self._default_path)
        custom_dir = self._resolve_template_dir(template_id, self._custom_path)
        if not default_dir.exists():
            raise FileNotFoundError(f"Default template not found for {template_id}")
        custom_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(default_dir / "template.j2", custom_dir / "template.j2")
        metadata_path = default_dir / "metadata.yaml"
        if metadata_path.exists():
            shutil.copy2(metadata_path, custom_dir / "metadata.yaml")

    def validate_directory(self, directory: Path) -> Dict[str, any]:
        metadata_path = directory / "metadata.yaml"
        template_path = directory / "template.j2"
        if not metadata_path.exists():
            raise FileNotFoundError(f"metadata.yaml not found in {directory}")
        if not template_path.exists():
            raise FileNotFoundError(f"template.j2 not found in {directory}")
        metadata = self._metadata_loader.load_metadata_path(metadata_path)
        template_path.read_text(encoding="utf-8")  # ensure readable
        return metadata.model_dump()

    def _resolve_template_dir(self, template_id: str, base_dir: Path) -> Path:
        parts = template_id.split("/")
        return base_dir.joinpath(*parts)

    def _resolve_path(self, home: Path, path: Path) -> Path:
        return (path if path.is_absolute() else (home / path)).resolve()

