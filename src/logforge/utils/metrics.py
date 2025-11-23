from __future__ import annotations

from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram


class MetricsRegistry:
    def __init__(self) -> None:
        self.registry = CollectorRegistry()

        self.events_generated_total = Counter(
            "logforge_events_generated_total",
            "Total number of events generated.",
            ["generator", "output"],
            registry=self.registry,
        )

        self.errors_total = Counter(
            "logforge_errors_total",
            "Total number of generator errors.",
            ["generator", "output"],
            registry=self.registry,
        )

        self.generators_running = Gauge(
            "logforge_generators_running",
            "Current number of generators in RUNNING state.",
            ["state"],
            registry=self.registry,
        )

        self.template_render_seconds = Histogram(
            "logforge_template_render_seconds",
            "Template render latency.",
            ["generator"],
            registry=self.registry,
            buckets=(0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1, 2, 5),
        )

        self.output_latency_seconds = Histogram(
            "logforge_output_latency_seconds",
            "Output handler latency.",
            ["handler"],
            registry=self.registry,
            buckets=(0.001, 0.01, 0.1, 0.5, 1, 2, 5, 10),
        )

        self.system_cpu_percent = Gauge(
            "logforge_system_cpu_percent",
            "System CPU utilisation percent.",
            registry=self.registry,
        )

        self.system_memory_mb = Gauge(
            "logforge_system_memory_megabytes",
            "Process resident memory usage in megabytes.",
            registry=self.registry,
        )

        self.system_threads = Gauge(
            "logforge_system_threads",
            "Active thread count for the LogForge process.",
            registry=self.registry,
        )

        self.output_buffer_size = Gauge(
            "logforge_output_buffer_size",
            "Buffered events awaiting delivery per handler.",
            ["handler"],
            registry=self.registry,
        )

        self.generator_last_emit_timestamp = Gauge(
            "logforge_generator_last_emit_timestamp",
            "Unix timestamp of last successful emit per output.",
            ["generator", "output"],
            registry=self.registry,
        )

    def record_generator_state(self, state_counts: dict[str, int]) -> None:
        for state, count in state_counts.items():
            self.generators_running.labels(state=state).set(count)

    def increment_events(self, generator: str, output: str) -> None:
        self.events_generated_total.labels(generator=generator, output=output).inc()

    def increment_errors(self, generator: str, output: str) -> None:
        self.errors_total.labels(generator=generator, output=output).inc()

    def observe_template_render(self, generator: str, duration: float) -> None:
        self.template_render_seconds.labels(generator=generator).observe(duration)

    def observe_output_latency(self, handler: str, duration: float) -> None:
        self.output_latency_seconds.labels(handler=handler).observe(duration)

    def set_system_metrics(self, cpu: float, memory_mb: float, threads: int) -> None:
        self.system_cpu_percent.set(cpu)
        self.system_memory_mb.set(memory_mb)
        self.system_threads.set(threads)

    def set_backlog(self, handler: str, size: int) -> None:
        self.output_buffer_size.labels(handler=handler).set(size)

    def set_last_emit(self, generator: str, output: str, timestamp: float) -> None:
        self.generator_last_emit_timestamp.labels(generator=generator, output=output).set(timestamp)

