"""Template update checking utilities."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional

from packaging.version import InvalidVersion, Version

from logforge.community.client import CommunityClient, CommunityClientConfig, CommunityClientError
from logforge.community.install import TemplateInstallError, install_template_archive
from logforge.templates.loader import TemplateLoader, TemplateRecord


@dataclass
class TemplateUpdateCandidate:
    """Represents a template that has an update available."""

    record: TemplateRecord
    latest_version: str
    remote_metadata: dict

    @property
    def template_id(self) -> str:
        return self.record.template_id

    @property
    def current_version(self) -> Optional[str]:
        return self.record.metadata.version

    @property
    def location(self) -> str:
        return self.record.location

    @property
    def metadata_path(self) -> Path:
        return self.record.metadata_path

    @property
    def template_path(self) -> Path:
        return self.record.template_path


class TemplateUpdateError(Exception):
    """Raised when template update checks fail."""


class TemplateUpdateChecker:
    """Compares local templates with community versions and installs updates."""

    def __init__(
        self,
        *,
        loader: Optional[TemplateLoader] = None,
        client: Optional[CommunityClient] = None,
        locations: Iterable[str] = ("default",),
    ) -> None:
        self.loader = loader or TemplateLoader()
        self.client = client or CommunityClient(CommunityClientConfig())
        self.locations = tuple(locations)

    def check_updates(
        self,
        template_ids: Optional[Iterable[str]] = None,
    ) -> List[TemplateUpdateCandidate]:
        """Return all templates that have newer versions upstream."""

        records = {record.template_id: record for record in self.loader.list_templates()}
        if template_ids:
            missing = sorted(set(template_ids) - records.keys())
            if missing:
                raise TemplateUpdateError(f"Template(s) not found locally: {', '.join(missing)}")
            targets = [records[template_id] for template_id in template_ids]
        else:
            targets = list(records.values())

        disallowed = [record.template_id for record in targets if record.location not in self.locations]
        if template_ids and disallowed:
            raise TemplateUpdateError(
                f"Template(s) cannot be updated automatically: {', '.join(disallowed)}"
            )

        candidates: List[TemplateUpdateCandidate] = []
        for record in targets:
            if record.location not in self.locations:
                continue
            try:
                remote = self.client.get_template_details(record.template_id)
            except CommunityClientError as exc:
                raise TemplateUpdateError(str(exc)) from exc
            remote_version = (
                remote.get("metadata", {}).get("version")
                or remote.get("version")
                or remote.get("latest_version")
            )
            if not isinstance(remote_version, str):
                continue
            if not self._is_newer(record.metadata.version, remote_version):
                continue
            candidates.append(
                TemplateUpdateCandidate(
                    record=record,
                    latest_version=remote_version,
                    remote_metadata=remote,
                )
            )
        return candidates

    def apply_update(self, candidate: TemplateUpdateCandidate, *, force: bool = True) -> Path:
        """Download and install the newer version for the provided candidate."""

        if candidate.location != "default":
            raise TemplateUpdateError("Updates are only supported for default templates.")
        try:
            archive = self.client.download_template(candidate.template_id)
        except CommunityClientError as exc:
            raise TemplateUpdateError(str(exc)) from exc
        destination = self.loader.default_dir
        try:
            installed_path = install_template_archive(
                candidate.template_id,
                archive,
                destination=destination,
                force=force,
            )
        except TemplateInstallError as exc:
            raise TemplateUpdateError(str(exc)) from exc
        self.loader.refresh()
        return installed_path

    @staticmethod
    def _is_newer(local: Optional[str], remote: str) -> bool:
        """Return True if the remote version is newer than the local version."""

        try:
            remote_version = Version(remote)
        except InvalidVersion:
            return local != remote
        if not local:
            return True
        try:
            local_version = Version(local)
        except InvalidVersion:
            return remote != local
        return remote_version > local_version


__all__ = ["TemplateUpdateChecker", "TemplateUpdateCandidate", "TemplateUpdateError"]

