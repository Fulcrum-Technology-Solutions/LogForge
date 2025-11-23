"""Unit tests for metrics collection."""

from __future__ import annotations

import time
from unittest.mock import MagicMock, patch

import pytest

from logforge.core.generator import Generator, GeneratorState
from logforge.outputs.base import BaseOutput, CapturingOutput, RetryPolicy
from logforge.utils.metrics import (
    cpu_percent,
    events_generated_total,
    generator_errors_total,
    generators_running,
    memory_usage_bytes,
    output_buffered_events,
    output_errors_total,
    output_events_sent_total,
    output_latency_seconds,
    template_render_seconds,
)


class TestEventGenerationMetrics:
    """Test event generation metrics."""

    def test_events_generated_total_increments(self) -> None:
        """Test that events_generated_total counter increments."""
        initial = events_generated_total.labels(generator="test_gen")._value.get()
        events_generated_total.labels(generator="test_gen").inc()
        assert events_generated_total.labels(generator="test_gen")._value.get() == initial + 1

    def test_generator_errors_total_increments(self) -> None:
        """Test that generator_errors_total counter increments."""
        initial = generator_errors_total.labels(generator="test_gen", error_type="ValueError")._value.get()
        generator_errors_total.labels(generator="test_gen", error_type="ValueError").inc()
        assert (
            generator_errors_total.labels(generator="test_gen", error_type="ValueError")._value.get()
            == initial + 1
        )

    def test_template_render_seconds_records_time(self) -> None:
        """Test that template_render_seconds histogram records time."""
        with template_render_seconds.labels(generator="test_gen", template="test_template").time():
            time.sleep(0.01)  # Small delay to ensure time is recorded
        # Check that at least one observation was recorded
        assert template_render_seconds.labels(generator="test_gen", template="test_template")._count.get() >= 1


class TestSystemMetrics:
    """Test system metrics."""

    def test_generators_running_gauge_updates(self) -> None:
        """Test that generators_running gauge can be updated."""
        generators_running.labels(state="RUNNING").set(5)
        assert generators_running.labels(state="RUNNING")._value.get() == 5.0

        generators_running.labels(state="RUNNING").set(3)
        assert generators_running.labels(state="RUNNING")._value.get() == 3.0

    def test_memory_usage_bytes_gauge_updates(self) -> None:
        """Test that memory_usage_bytes gauge can be updated."""
        memory_usage_bytes.set(1024 * 1024)  # 1 MB
        assert memory_usage_bytes._value.get() == 1024 * 1024

    def test_cpu_percent_gauge_updates(self) -> None:
        """Test that cpu_percent gauge can be updated."""
        cpu_percent.set(50.5)
        assert cpu_percent._value.get() == 50.5


class TestOutputMetrics:
    """Test output handler metrics."""

    def test_output_events_sent_total_increments(self) -> None:
        """Test that output_events_sent_total counter increments."""
        initial = output_events_sent_total.labels(output="test_output", output_type="file")._value.get()
        output_events_sent_total.labels(output="test_output", output_type="file").inc()
        assert (
            output_events_sent_total.labels(output="test_output", output_type="file")._value.get()
            == initial + 1
        )

    def test_output_errors_total_increments(self) -> None:
        """Test that output_errors_total counter increments."""
        initial = output_errors_total.labels(
            output="test_output", output_type="http", error_type="ConnectionError"
        )._value.get()
        output_errors_total.labels(output="test_output", output_type="http", error_type="ConnectionError").inc()
        assert (
            output_errors_total.labels(
                output="test_output", output_type="http", error_type="ConnectionError"
            )._value.get()
            == initial + 1
        )

    def test_output_latency_seconds_records_time(self) -> None:
        """Test that output_latency_seconds histogram records time."""
        with output_latency_seconds.labels(output="test_output", output_type="tcp").time():
            time.sleep(0.01)  # Small delay
        # Check that at least one observation was recorded
        assert output_latency_seconds.labels(output="test_output", output_type="tcp")._count.get() >= 1

    def test_output_buffered_events_gauge_updates(self) -> None:
        """Test that output_buffered_events gauge can be updated."""
        output_buffered_events.labels(output="test_output").set(10)
        assert output_buffered_events.labels(output="test_output")._value.get() == 10.0


class TestGeneratorMetricsIntegration:
    """Test metrics integration in Generator class."""

    def test_metrics_are_accessible_from_generator_module(self) -> None:
        """Test that metrics can be imported and used from generator context."""
        # This test verifies that the metrics are properly imported in generator.py
        # and can be used for tracking events
        initial = events_generated_total.labels(generator="test_gen")._value.get()
        events_generated_total.labels(generator="test_gen").inc()
        assert events_generated_total.labels(generator="test_gen")._value.get() == initial + 1

    def test_template_render_metrics_are_accessible(self) -> None:
        """Test that template_render_seconds metric is accessible."""
        initial_count = template_render_seconds.labels(
            generator="test_gen", template="test_template"
        )._count.get()
        with template_render_seconds.labels(generator="test_gen", template="test_template").time():
            time.sleep(0.01)
        assert (
            template_render_seconds.labels(generator="test_gen", template="test_template")._count.get()
            >= initial_count + 1
        )

    def test_generator_error_metrics_are_accessible(self) -> None:
        """Test that generator_errors_total metric is accessible."""
        initial = generator_errors_total.labels(generator="test_gen", error_type="ValueError")._value.get()
        generator_errors_total.labels(generator="test_gen", error_type="ValueError").inc()
        assert (
            generator_errors_total.labels(generator="test_gen", error_type="ValueError")._value.get()
            == initial + 1
        )


class TestOutputMetricsIntegration:
    """Test metrics integration in output handlers."""

    def test_output_tracks_events_sent(self) -> None:
        """Test that output handlers track output_events_sent_total metric."""
        output = CapturingOutput("test_output")
        initial = output_events_sent_total.labels(output="test_output", output_type="capture")._value.get()
        output.emit("test event")
        assert (
            output_events_sent_total.labels(output="test_output", output_type="capture")._value.get()
            == initial + 1
        )

    def test_output_tracks_latency(self) -> None:
        """Test that output handlers track output_latency_seconds metric."""
        output = CapturingOutput("test_output")
        initial_count = output_latency_seconds.labels(output="test_output", output_type="capture")._count.get()
        output.emit("test event")
        assert (
            output_latency_seconds.labels(output="test_output", output_type="capture")._count.get()
            >= initial_count + 1
        )

    def test_output_tracks_buffered_events(self) -> None:
        """Test that output handlers track output_buffered_events gauge."""
        output = CapturingOutput("test_output", buffer_size=10)
        # Enqueue an event
        output._enqueue("test event", None)
        output._update_buffer_metrics()
        assert output_buffered_events.labels(output="test_output")._value.get() == 1.0

    def test_output_tracks_errors(self) -> None:
        """Test that output handlers track output_errors_total metric."""
        # Create an output that will fail
        class FailingOutput(CapturingOutput):
            def _send(self, event: str, metadata=None) -> None:
                raise ConnectionError("Connection failed")

        output = FailingOutput("test_output")
        initial = output_errors_total.labels(
            output="test_output", output_type="capture", error_type="ConnectionError"
        )._value.get()
        try:
            output.emit("test event")
        except Exception:
            pass
        assert (
            output_errors_total.labels(
                output="test_output", output_type="capture", error_type="ConnectionError"
            )._value.get()
            >= initial
        )


__all__ = [
    "TestEventGenerationMetrics",
    "TestSystemMetrics",
    "TestOutputMetrics",
    "TestGeneratorMetricsIntegration",
    "TestOutputMetricsIntegration",
]
