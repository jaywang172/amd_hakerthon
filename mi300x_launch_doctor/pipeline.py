from __future__ import annotations

import json
from pathlib import Path

from mi300x_launch_doctor.benchmark.results import load_benchmark
from mi300x_launch_doctor.generator.dockerfile import generate_dockerfile
from mi300x_launch_doctor.generator.requirements import generate_requirements
from mi300x_launch_doctor.generator.vllm_script import generate_vllm_script
from mi300x_launch_doctor.intake.inventory import build_inventory, filter_runtime_files, iter_scannable_files
from mi300x_launch_doctor.intake.repo import cleanup_source, github_repo_name, is_github_url, prepare_source, prepare_uploaded_path
from mi300x_launch_doctor.report.markdown import generate_markdown_report
from mi300x_launch_doctor.scanner.scan_files import scan_files
from mi300x_launch_doctor.scoring.readiness import score_readiness
from mi300x_launch_doctor.schemas import GeneratedFile, ScanResult


def analyze_source(
    source: str,
    output_dir: str | Path = "generated",
    benchmark_json: str | None = None,
    write_artifacts: bool = True,
    scan_mode: str = "runtime",
) -> ScanResult:
    prepared = prepare_source(source)
    try:
        return analyze_prepared_source(
            root=prepared.root,
            source_label=prepared.source_label,
            repo_name=github_repo_name(source) if is_github_url(source) else prepared.root.name,
            output_dir=output_dir,
            benchmark_json=benchmark_json,
            write_artifacts=write_artifacts,
            scan_mode=scan_mode,
        )
    finally:
        cleanup_source(prepared)


def analyze_uploaded_path(
    uploaded_path: str,
    output_dir: str | Path = "generated",
    benchmark_json: str | None = None,
    write_artifacts: bool = True,
    scan_mode: str = "runtime",
) -> ScanResult:
    prepared = prepare_uploaded_path(uploaded_path)
    try:
        return analyze_prepared_source(
            root=prepared.root,
            source_label=prepared.source_label,
            repo_name=prepared.root.name,
            output_dir=output_dir,
            benchmark_json=benchmark_json,
            write_artifacts=write_artifacts,
            scan_mode=scan_mode,
        )
    finally:
        cleanup_source(prepared)


def analyze_prepared_source(
    root: Path,
    source_label: str,
    repo_name: str,
    output_dir: str | Path = "generated",
    benchmark_json: str | None = None,
    write_artifacts: bool = True,
    scan_mode: str = "runtime",
) -> ScanResult:
    root = root.resolve()
    all_files = iter_scannable_files(root)
    files, scan_scope = scoped_files(root, all_files, scan_mode)
    inventory = build_inventory(root, source_label, repo_name, files, scan_scope=scan_scope)
    risks = scan_files(root, files)
    score = score_readiness(inventory, risks)
    benchmark = load_benchmark(benchmark_json)

    generated = [
        generate_dockerfile(),
        generate_requirements(root, files),
        generate_vllm_script(),
    ]
    report = generate_markdown_report(
        inventory=inventory,
        risks=risks,
        score=score,
        benchmark=benchmark,
        generated_file_names=[item.name for item in generated] + ["scan_result.json"],
    )
    generated.append(report)

    result = ScanResult(
        inventory=inventory,
        risks=risks,
        score=score,
        generated_files=generated,
        benchmark=benchmark,
    )
    if write_artifacts:
        write_generated_artifacts(result, output_dir)
    return result


def scoped_files(root: Path, files: list[Path], scan_mode: str) -> tuple[list[Path], str]:
    normalized = scan_mode.strip().lower().replace("_", "-") if scan_mode else "runtime"
    if normalized in {"full", "full-repository-audit", "full repository audit"}:
        return files, "Full repository audit"
    return filter_runtime_files(root, files), "Runtime deployment scan"


def write_generated_artifacts(result: ScanResult, output_dir: str | Path) -> list[Path]:
    output_path = Path(output_dir)
    written: list[Path] = []
    for item in result.generated_files:
        written_path = item.write_to(output_path)
        if item.name.endswith(".sh"):
            written_path.chmod(0o755)
        written.append(written_path)
    scan_json = output_path / "scan_result.json"
    scan_json.write_text(json.dumps(result.to_dict(), indent=2), encoding="utf-8")
    written.append(scan_json)
    return written


def generated_file_map(result: ScanResult) -> dict[str, GeneratedFile]:
    return {item.name: item for item in result.generated_files}
