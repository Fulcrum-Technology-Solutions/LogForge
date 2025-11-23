"""Prometheus metrics collection for LogForge."""

from __future__ import annotations

from prometheus_client import Counter, Gauge, Histogram

# Event generation metrics
events_generated_total = Counter(
    "logforge_events_generated_total",
    "Total number of events generated",
    ["generator"],
)

generator_errors_total = Counter(
    "logforge_generator_errors_total",
    "Total number of generator errors",
    ["generator", "error_type"],
)

# System metrics
generators_running = Gauge(
    "logforge_generators_running",
    "Number of generators currently running",
    ["state"],
)

memory_usage_bytes = Gauge(
    "logforge_memory_usage_bytes",
    "Memory usage in bytes",
)

cpu_percent = Gauge(
    "logforge_cpu_percent",
    "CPU usage percentage",
)

# Performance metrics
template_render_seconds = Histogram(
    "logforge_template_render_seconds",
    "Time taken to render templates",
    ["generator", "template"],
    buckets=(0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0),
)

output_latency_seconds = Histogram(
    "logforge_output_latency_seconds",
    "Time taken to send events to outputs",
    ["output", "output_type"],
    buckets=(0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0, 10.0),
)

output_events_sent_total = Counter(
    "logforge_output_events_sent_total",
    "Total number of events sent to outputs",
    ["output", "output_type"],
)

output_errors_total = Counter(
    "logforge_output_errors_total",
    "Total number of output errors",
    ["output", "output_type", "error_type"],
)

output_buffered_events = Gauge(
    "logforge_output_buffered_events",
    "Number of events currently buffered",
    ["output"],
)

__all__ = [
    "events_generated_total",
    "generator_errors_total",
    "generators_running",
    "memory_usage_bytes",
    "cpu_percent",
    "template_render_seconds",
    "output_latency_seconds",
    "output_events_sent_total",
    "output_errors_total",
    "output_buffered_events",
]
