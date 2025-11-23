"""Utilities for installing community templates."""

from __future__ import annotations

import shutil
import tempfile
import zipfile
from pathlib import Path

from logforge.core.home import resolve_logforge_home


class TemplateInstallError(Exception):
    """Raised when a template package cannot be installed."""


def install_template_archive(
    template_id: str,
    archive_bytes: bytes,
    *,
    destination: Path | None = None,
    force: bool = False,
) -> Path:
    """Install a template archive into the custom templates directory."""

    base_dir = destination or resolve_logforge_home() / "templates" / "custom"
    target_dir = base_dir / template_id
    if target_dir.exists():
        if not force:
            raise TemplateInstallError(
                f"Template '{template_id}' already exists at {target_dir}. Use force to overwrite."
            )
        shutil.rmtree(target_dir)
    base_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir) / "package.zip"
        tmp_path.write_bytes(archive_bytes)
        if not zipfile.is_zipfile(tmp_path):
            raise TemplateInstallError("Downloaded package is not a valid ZIP archive.")
        extracted_dir = Path(tmpdir) / "contents"
        with zipfile.ZipFile(tmp_path) as zf:
            zf.extractall(extracted_dir)
        metadata_path = extracted_dir / "metadata.yaml"
        template_path = extracted_dir / "template.j2"
        if not metadata_path.exists() or not template_path.exists():
            raise TemplateInstallError("Package missing metadata.yaml or template.j2.")
        shutil.copytree(extracted_dir, target_dir)
    return target_dir


__all__ = ["install_template_archive", "TemplateInstallError"]
