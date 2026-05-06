from __future__ import annotations

from collections import Counter

from mi300x_launch_doctor.schemas import BenchmarkResult, GeneratedFile, RepoInventory, RiskItem, ScoreResult


def generate_markdown_report(
    inventory: RepoInventory,
    risks: list[RiskItem],
    score: ScoreResult,
    benchmark: BenchmarkResult,
    generated_file_names: list[str],
) -> GeneratedFile:
    content = "\n".join(
        [
            "# AMD MI300X Deployment Report",
            "",
            "## Summary",
            f"Readiness Score: **{score.score}/100 — {score.label}**",
            "",
            "MI300X Launch Doctor is not a CUDA-to-ROCm translator. It is a deployment readiness system that helps teams decide whether an AI workload can run on AMD, what must change, and how to validate it.",
            "",
            "## Detected Stack",
            f"- Source: `{inventory.source}`",
            f"- Scan scope: {inventory.scan_scope}",
            f"- Files scanned: {inventory.files_scanned}",
            f"- Languages: {', '.join(inventory.languages) if inventory.languages else 'Unknown'}",
            f"- Frameworks: {', '.join(inventory.frameworks) if inventory.frameworks else 'Unknown'}",
            "",
            "## ROCm Deployment Recommendation",
            "Recommended inference path: **vLLM on ROCm Docker**",
            "",
            "Use the generated `run_vllm_amd.sh` script as the starting point for MI300X inference validation.",
            "",
            "## Risk Summary",
            risk_summary_table(risks),
            "",
            "## Major Risks",
            risk_detail_section(risks),
            "",
            "## Score Notes",
            score_notes(score),
            "",
            "## Generated Files",
            "\n".join(f"- `{name}`" for name in generated_file_names),
            "",
            "## Benchmark",
            benchmark_section(benchmark),
            "",
            "## Hackathon Deadline Note",
            "Working deadline: May 11, 2026 03:00 Taipei time, pending final confirmation from the Event Schedule tab.",
            "",
        ]
    )
    return GeneratedFile(name="AMD_DEPLOYMENT_REPORT.md", path="generated/AMD_DEPLOYMENT_REPORT.md", content=content)


def risk_summary_table(risks: list[RiskItem]) -> str:
    if not risks:
        return "No ROCm deployment risks were detected by the v1 static scanner."
    counts = Counter((risk.severity, risk.category) for risk in risks)
    rows = ["| Severity | Category | Count |", "| --- | --- | --- |"]
    for (severity, category), count in sorted(counts.items()):
        rows.append(f"| {severity} | {category} | {count} |")
    return "\n".join(rows)


def risk_detail_section(risks: list[RiskItem]) -> str:
    if not risks:
        return "No major risks found."
    lines: list[str] = []
    ordered = sorted(risks, key=lambda risk: severity_rank(risk.severity))
    for index, risk in enumerate(ordered[:25], start=1):
        location = f"{risk.file}:{risk.line}" if risk.line else risk.file
        lines.extend(
            [
                f"{index}. **{risk.severity.upper()} — {risk.category}**",
                f"   - File: `{location}`",
                f"   - Evidence: `{risk.evidence}`",
                f"   - Why it matters: {risk.why_it_matters}",
                f"   - Recommendation: {risk.recommendation}",
            ]
        )
    if len(risks) > 25:
        lines.append(f"\nAdditional findings omitted from report preview: {len(risks) - 25}")
    return "\n".join(lines)


def score_notes(score: ScoreResult) -> str:
    lines: list[str] = []
    if score.bonus_reasons:
        lines.append("Bonuses:")
        lines.extend(f"- {reason}" for reason in score.bonus_reasons)
    if score.penalty_summary:
        lines.append("")
        lines.append("Penalty summary:")
        lines.extend(f"- {key}: -{value}" for key, value in score.penalty_summary.items())
    return "\n".join(lines) if lines else "No scoring notes."


def benchmark_section(benchmark: BenchmarkResult) -> str:
    lines = [
        f"- Benchmark Status: **{benchmark.status_label}**",
        f"- Model: `{benchmark.model}`",
        f"- Backend: `{benchmark.backend}`",
        f"- GPU: `{benchmark.gpu}`",
        f"- Load success: `{benchmark.load_success}`",
    ]
    if benchmark.avg_latency_ms is not None:
        lines.append(f"- Average latency: {benchmark.avg_latency_ms:.1f} ms")
    if benchmark.p50_latency_ms is not None:
        lines.append(f"- p50 latency: {benchmark.p50_latency_ms:.1f} ms")
    if benchmark.p95_latency_ms is not None:
        lines.append(f"- p95 latency: {benchmark.p95_latency_ms:.1f} ms")
    if benchmark.tokens_per_second is not None:
        lines.append(f"- Throughput: {benchmark.tokens_per_second:.1f} tokens/sec")
    if benchmark.memory_used_gb is not None:
        lines.append(f"- GPU memory used: {benchmark.memory_used_gb:.1f} GB")
    if benchmark.disclaimer:
        lines.append(f"- Disclaimer: {benchmark.disclaimer}")
    return "\n".join(lines)


def severity_rank(severity: str) -> int:
    return {"high": 0, "medium": 1, "low": 2}.get(severity, 3)
