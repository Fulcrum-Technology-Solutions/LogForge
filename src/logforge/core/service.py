"""LogForge service that coordinates all components."""

from __future__ import annotations

import logging
import multiprocessing
import os
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Optional

import psutil

from logforge.core.config import load_validated_config
from logforge.core.config_schema import ConfigModel
from logforge.core.engine import GeneratorEngine, OutputFactory
from logforge.entities.registry import EntityRegistry
from logforge.templates.loader import TemplateLoader
from logforge.templates.renderer import TemplateRenderer
from logforge.utils.metrics import cpu_percent, memory_usage_bytes


class LogForgeService:
    """Main service that coordinates all LogForge components."""

    def __init__(
        self,
        config: ConfigModel,
        *,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        self.config = config
        self._logger = logger or logging.getLogger("logforge.service")
        self._thread_pool: Optional[ThreadPoolExecutor] = None
        self._metrics_thread: Optional[threading.Thread] = None
        self._metrics_stop_event = threading.Event()
        self._process = psutil.Process(os.getpid())

        # Initialize components
        from logforge.entities.storage import EntityStorage
        from pathlib import Path

        # Entity registry with config
        entity_storage = EntityStorage(
            path=Path(config.entity_registry.path),
            backup_count=config.entity_registry.backup_count if config.entity_registry.backup_enabled else 0,
            autosave_interval=config.entity_registry.save_interval,
        )
        self.entity_registry = EntityRegistry(
            storage=entity_storage,
            autosave=config.entity_registry.auto_save,
        )

        # Template loader with config
        self.template_loader = TemplateLoader(
            templates_dir=Path(config.templates.local_path),
            precedence=config.templates.precedence,
            cache_ttl=config.templates.cache_ttl,
        )

        # Template renderer needs entity registry access
        from logforge.entities import functions as registry_functions
        registry_functions._set_registry(self.entity_registry)

        self.template_renderer = TemplateRenderer(loader=self.template_loader)
        self.output_factory = OutputFactory(config.outputs)
        self.engine = GeneratorEngine.from_config(config, self.template_renderer)

        # Calculate thread pool size
        pool_size = config.engine.thread_pool_size
        if pool_size is None:
            # Default: CPU cores × 5
            pool_size = multiprocessing.cpu_count() * 5
        self._thread_pool = ThreadPoolExecutor(max_workers=pool_size, thread_name_prefix="logforge")

    @classmethod
    def from_config_path(
        cls,
        config_path: Optional[Path] = None,
        *,
        logger: Optional[logging.Logger] = None,
    ) -> LogForgeService:
        """Create service from configuration file."""
        config = load_validated_config(config_path)
        return cls(config, logger=logger)

    def start(self) -> None:
        """Start the service and all enabled generators."""
        self._logger.info("Starting LogForge service")
        self.engine.start_all()
        # Start metrics collection thread
        self._metrics_stop_event.clear()
        self._metrics_thread = threading.Thread(
            target=self._update_system_metrics_loop,
            name="logforge-metrics",
            daemon=True,
        )
        self._metrics_thread.start()

    def stop(self, timeout: float = 10.0) -> None:
        """Stop the service and all generators."""
        self._logger.info("Stopping LogForge service")
        # Stop metrics collection
        self._metrics_stop_event.set()
        if self._metrics_thread:
            self._metrics_thread.join(timeout=2.0)
        self.engine.stop_all()
        if self._thread_pool:
            self._thread_pool.shutdown(wait=True, timeout=timeout)

    def _update_system_metrics_loop(self) -> None:
        """Background thread that periodically updates system metrics."""
        while not self._metrics_stop_event.wait(5.0):  # Update every 5 seconds
            try:
                # Update memory usage
                memory_info = self._process.memory_info()
                memory_usage_bytes.set(memory_info.rss)

                # Update CPU usage (non-blocking)
                cpu_usage = self._process.cpu_percent(interval=None)
                cpu_percent.set(cpu_usage)
            except Exception as exc:
                self._logger.warning("Failed to update system metrics: %s", exc)

    def __enter__(self) -> LogForgeService:
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.stop()


__all__ = ["LogForgeService"]
