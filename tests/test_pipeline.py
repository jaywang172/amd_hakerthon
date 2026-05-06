from pathlib import Path

from mi300x_launch_doctor.pipeline import analyze_source


def test_cli_pipeline_writes_generated_artifacts(tmp_path):
    result = analyze_source("fixtures/cuda_risk_repo", output_dir=tmp_path)

    assert result.score.score < 100
    assert (tmp_path / "AMD_DEPLOYMENT_REPORT.md").exists()
    assert (tmp_path / "Dockerfile.rocm").exists()
    assert (tmp_path / "requirements-rocm.txt").exists()
    assert (tmp_path / "run_vllm_amd.sh").exists()
    assert (tmp_path / "scan_result.json").exists()


def test_pipeline_uses_real_benchmark_json_when_supplied(tmp_path):
    benchmark_path = tmp_path / "benchmark.json"
    benchmark_path.write_text(
        '{"model":"demo","backend":"vLLM ROCm","gpu":"AMD Instinct MI300X","load_success":true,"tokens_per_second":12.5}',
        encoding="utf-8",
    )
    result = analyze_source("fixtures/rocm_ready_repo", output_dir=tmp_path / "out", benchmark_json=str(benchmark_path))

    assert result.benchmark.benchmark_mode == "real"
    assert result.benchmark.status_label == "Real Run"
    assert result.benchmark.tokens_per_second == 12.5
