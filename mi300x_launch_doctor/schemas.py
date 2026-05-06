from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal


Severity = Literal["high", "medium", "low"]
BenchmarkMode = Literal["real", "sample"]


@dataclass(frozen=True)
class RiskItem:
    severity: Severity
    category: str
    file: str
    evidence: str
    why_it_matters: str
    recommendation: str
    line: int | None = None
    rule_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "severity": self.severity,
            "category": self.category,
            "file": self.file,
            "line": self.line,
            "evidence": self.evidence,
            "why_it_matters": self.why_it_matters,
            "recommendation": self.recommendation,
            "rule_id": self.rule_id,
        }


@dataclass(frozen=True)
class BenchmarkResult:
    benchmark_mode: BenchmarkMode
    model: str
    backend: str
    gpu: str
    load_success: bool
    avg_latency_ms: float | None = None
    p50_latency_ms: float | None = None
    p95_latency_ms: float | None = None
    tokens_per_second: float | None = None
    memory_used_gb: float | None = None
    disclaimer: str | None = None

    @property
    def status_label(self) -> str:
        if self.benchmark_mode == "real":
            return "Real Run"
        return "Sample / Expected Format"

    def to_dict(self) -> dict[str, Any]:
        return {
            "benchmark_mode": self.benchmark_mode,
            "benchmark_status": self.status_label,
            "model": self.model,
            "backend": self.backend,
            "gpu": self.gpu,
            "load_success": self.load_success,
            "avg_latency_ms": self.avg_latency_ms,
            "p50_latency_ms": self.p50_latency_ms,
            "p95_latency_ms": self.p95_latency_ms,
            "tokens_per_second": self.tokens_per_second,
            "memory_used_gb": self.memory_used_gb,
            "disclaimer": self.disclaimer,
        }


@dataclass(frozen=True)
class GeneratedFile:
    name: str
    path: str
    content: str

    def write_to(self, output_dir: Path) -> Path:
        output_dir.mkdir(parents=True, exist_ok=True)
        target = output_dir / self.name
        target.write_text(self.content, encoding="utf-8")
        return target

    def to_dict(self) -> dict[str, str]:
        return {
            "name": self.name,
            "path": self.path,
            "content": self.content,
        }


@dataclass(frozen=True)
class RepoInventory:
    repo_name: str
    source: str
    root_path: str
    scan_scope: str
    files_scanned: int
    important_files: list[str]
    languages: list[str]
    frameworks: list[str]
    files_discovered: int | None = None
    files_omitted_by_limit: int = 0
    scan_limit_applied: bool = False
    has_dockerfile: bool = False
    has_requirements: bool = False
    uses_pytorch: bool = False
    has_inference_script: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "repo_name": self.repo_name,
            "source": self.source,
            "root_path": self.root_path,
            "scan_scope": self.scan_scope,
            "files_scanned": self.files_scanned,
            "files_discovered": self.files_discovered,
            "files_omitted_by_limit": self.files_omitted_by_limit,
            "scan_limit_applied": self.scan_limit_applied,
            "important_files": self.important_files,
            "languages": self.languages,
            "frameworks": self.frameworks,
            "has_dockerfile": self.has_dockerfile,
            "has_requirements": self.has_requirements,
            "uses_pytorch": self.uses_pytorch,
            "has_inference_script": self.has_inference_script,
        }


@dataclass(frozen=True)
class ScoreResult:
    score: int
    label: str
    bonus_reasons: list[str] = field(default_factory=list)
    penalty_summary: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "score": self.score,
            "label": self.label,
            "bonus_reasons": self.bonus_reasons,
            "penalty_summary": self.penalty_summary,
        }


@dataclass(frozen=True)
class ScanResult:
    inventory: RepoInventory
    risks: list[RiskItem]
    score: ScoreResult
    generated_files: list[GeneratedFile]
    benchmark: BenchmarkResult

    def to_dict(self) -> dict[str, Any]:
        return {
            "inventory": self.inventory.to_dict(),
            "score": self.score.to_dict(),
            "risk_items": [risk.to_dict() for risk in self.risks],
            "generated_files": [generated.to_dict() for generated in self.generated_files],
            "benchmark": self.benchmark.to_dict(),
        }
