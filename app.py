from __future__ import annotations

import shutil
import tempfile
import os
from pathlib import Path
from typing import Any

import gradio as gr

from mi300x_launch_doctor.pipeline import analyze_prepared_source, analyze_source
from mi300x_launch_doctor.schemas import ScanResult


SAMPLE_REPO = str((Path(__file__).parent / "fixtures" / "cuda_risk_repo").resolve())


def analyze(repo_or_path: str, uploaded_files: list[Any] | None, benchmark_json: Any | None, scan_mode_label: str = "Runtime deployment scan") -> tuple[str, list[list[Any]], str, str, str, str, list[str]]:
    output_dir = Path(tempfile.mkdtemp(prefix="mi300x-generated-"))
    benchmark_path = uploaded_file_path(benchmark_json)
    scan_mode = scan_mode_value(scan_mode_label)

    try:
        if uploaded_files:
            source_root = prepare_upload_bundle(uploaded_files)
            result = analyze_prepared_source(
                root=source_root,
                source_label="uploaded files",
                repo_name="uploaded-files",
                output_dir=output_dir,
                benchmark_json=benchmark_path,
                scan_mode=scan_mode,
            )
        elif repo_or_path and repo_or_path.strip():
            result = analyze_source(repo_or_path.strip(), output_dir=output_dir, benchmark_json=benchmark_path, scan_mode=scan_mode)
        else:
            result = analyze_source(SAMPLE_REPO, output_dir=output_dir, benchmark_json=benchmark_path, scan_mode=scan_mode)
    except Exception as exc:
        return format_error_outputs(str(exc))

    return format_outputs(result, output_dir)


def use_sample() -> str:
    return SAMPLE_REPO


def prepare_upload_bundle(uploaded_files: list[Any]) -> Path:
    bundle = Path(tempfile.mkdtemp(prefix="mi300x-upload-bundle-"))
    for uploaded in uploaded_files:
        path = Path(uploaded_file_path(uploaded))
        if path.suffix.lower() == ".zip" and len(uploaded_files) == 1:
            shutil.unpack_archive(str(path), str(bundle))
            children = [child for child in bundle.iterdir() if child.is_dir()]
            return children[0] if len(children) == 1 else bundle
        shutil.copy2(path, bundle / path.name)
    return bundle


def uploaded_file_path(uploaded: Any | None) -> str | None:
    if uploaded is None:
        return None
    if isinstance(uploaded, str):
        return uploaded
    return getattr(uploaded, "name", None)


def scan_mode_value(label: str) -> str:
    if label == "Full repository audit":
        return "full"
    return "runtime"


def format_outputs(result: ScanResult, output_dir: Path) -> tuple[str, list[list[Any]], str, str, str, str, list[str]]:
    top_risks = top_deployment_blockers(result.risks, limit=10)
    omitted = max(0, len(result.risks) - len(top_risks))
    score_md = "\n".join(
        [
            f"## {result.score.score}/100",
            f"**{result.score.label}**",
            "",
            f"Scan scope: **{result.inventory.scan_scope}**",
            f"Benchmark Status: **{result.benchmark.status_label}**",
            f"Showing top {len(top_risks)} deployment blockers. Additional findings omitted: {omitted}.",
        ]
    )
    risks = [
        [
            risk.severity,
            risk.category,
            risk.file,
            risk.line or "",
            risk.evidence,
            risk.recommendation,
        ]
        for risk in top_risks
    ]
    file_content = {item.name: item.content for item in result.generated_files}
    downloads = [str(output_dir / name) for name in ["AMD_DEPLOYMENT_REPORT.md", "Dockerfile.rocm", "requirements-rocm.txt", "run_vllm_amd.sh", "scan_result.json"]]
    return (
        score_md,
        risks,
        file_content.get("AMD_DEPLOYMENT_REPORT.md", ""),
        file_content.get("Dockerfile.rocm", ""),
        file_content.get("requirements-rocm.txt", ""),
        file_content.get("run_vllm_amd.sh", ""),
        downloads,
    )


def top_deployment_blockers(risks: list[Any], limit: int = 10) -> list[Any]:
    return sorted(risks, key=risk_sort_key)[:limit]


def risk_sort_key(risk: Any) -> tuple[int, int, str, int]:
    severity_rank = {"high": 0, "medium": 1, "low": 2}.get(risk.severity, 3)
    category_rank = {
        "docker_base_image": 0,
        "dependency": 1,
        "quantization": 1,
        "native_cuda": 2,
        "cuda_api": 3,
        "hardcoded_device": 4,
        "docker_runtime": 5,
        "system_command": 6,
        "inference_engine": 7,
    }.get(risk.category, 8)
    return severity_rank, category_rank, risk.file, risk.line or 0


def format_error_outputs(message: str) -> tuple[str, list[list[Any]], str, str, str, str, list[str]]:
    safe_message = message.strip() or "Unknown analysis error."
    score_md = "\n".join(
        [
            "## Analysis Error",
            "**The input could not be scanned.**",
            "",
            safe_message,
            "",
            "Try a public GitHub repository URL, a local folder path, an uploaded zip, or the built-in sample repo.",
        ]
    )
    report = "\n".join(
        [
            "# Analysis Error",
            "",
            safe_message,
            "",
            "No deployment artifacts were generated for this input.",
        ]
    )
    return score_md, [], report, "", "", "", []


with gr.Blocks(title="MI300X Launch Doctor") as demo:
    gr.Markdown(
        """
# MI300X Launch Doctor
AI-powered ROCm deployment readiness for AMD MI300X.
"""
    )
    with gr.Row():
        repo_input = gr.Textbox(label="GitHub repo URL or local path", placeholder="https://github.com/org/repo")
        sample_button = gr.Button("Use sample repo")
    uploads = gr.Files(label="Uploaded zip or selected files", file_count="multiple")
    benchmark_upload = gr.File(label="Optional real benchmark JSON", file_types=[".json"])
    scan_mode = gr.Radio(
        choices=["Runtime deployment scan", "Full repository audit"],
        value="Runtime deployment scan",
        label="Scan Mode",
    )
    analyze_button = gr.Button("Analyze", variant="primary")

    score_output = gr.Markdown(label="Readiness Score")
    risk_table = gr.Dataframe(
        headers=["Severity", "Category", "File", "Line", "Evidence", "Recommendation"],
        label="Top Deployment Blockers",
        wrap=True,
    )
    report_preview = gr.Markdown(label="AMD Deployment Report")
    with gr.Tabs():
        with gr.Tab("Dockerfile.rocm"):
            docker_preview = gr.Code(language="dockerfile")
        with gr.Tab("requirements-rocm.txt"):
            requirements_preview = gr.Textbox(lines=18, show_label=False)
        with gr.Tab("run_vllm_amd.sh"):
            script_preview = gr.Code(language="shell")
    downloads = gr.Files(label="Download generated deployment pack")

    sample_button.click(fn=use_sample, outputs=repo_input)
    analyze_button.click(
        fn=analyze,
        inputs=[repo_input, uploads, benchmark_upload, scan_mode],
        outputs=[score_output, risk_table, report_preview, docker_preview, requirements_preview, script_preview, downloads],
    )


if __name__ == "__main__":
    port = int(os.environ.get("GRADIO_SERVER_PORT", "7860"))
    demo.launch(server_name="0.0.0.0", server_port=port)
