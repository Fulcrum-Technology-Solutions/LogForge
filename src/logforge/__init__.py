"""LogForge package root."""

from importlib.metadata import PackageNotFoundError, version

__all__ = ["__version__", "get_version"]

try:
    __version__ = version("logforge")
except PackageNotFoundError:  # pragma: no cover - fallback during local dev
    __version__ = "0.0.0"


def get_version() -> str:
    """Return the installed LogForge package version."""
    return __version__
