from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from mi300x_launch_doctor.schemas import BenchmarkResult


SAMPLE_DISCLAIMER = "Sample benchmark format for demo using Qwen3.5-0.8B as the default MI300X/vLLM validation target. Replace with real AMD Developer Cloud output when available."


def sample_benchmark() -> BenchmarkResult:
    return BenchmarkResult(
        benchmark_mode="sample",
        model="Qwen/Qwen3.5-0.8B",
        backend="vLLM ROCm",
        gpu="AMD Instinct MI300X",
        load_success=True,
        avg_latency_ms=742.0,
        p50_latency_ms=690.0,
        p95_latency_ms=1103.0,
        tokens_per_second=68.4,
        memory_used_gb=18.2,
        disclaimer=SAMPLE_DISCLAIMER,
    )


def load_benchmark(path: str | None) -> BenchmarkResult:
    if not path:
        return sample_benchmark()
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return BenchmarkResult(
        benchmark_mode="real",
        model=str(data.get("model", "unknown")),
        backend=str(data.get("backend", "vLLM ROCm")),
        gpu=str(data.get("gpu", "AMD Instinct MI300X")),
        load_success=bool(data.get("load_success", False)),
        avg_latency_ms=_optional_float(data.get("avg_latency_ms")),
        p50_latency_ms=_optional_float(data.get("p50_latency_ms")),
        p95_latency_ms=_optional_float(data.get("p95_latency_ms")),
        tokens_per_second=_optional_float(data.get("tokens_per_second")),
        memory_used_gb=_optional_float(data.get("memory_used_gb")),
        disclaimer=None,
    )


def _optional_float(value: Any) -> float | None:
    if value is None:
        return None
    return float(value)
