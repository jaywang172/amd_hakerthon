from pathlib import Path

from mi300x_launch_doctor.pipeline import analyze_source
from mi300x_launch_doctor.intake.inventory import MAX_SCAN_FILES


def test_runtime_scan_excludes_docs_noise(tmp_path):
    repo = tmp_path / "repo"
    (repo / "docs").mkdir(parents=True)
    (repo / "src").mkdir()
    (repo / "docs" / "guide.md").write_text("Use CUDA_VISIBLE_DEVICES=0 in this tutorial.\n", encoding="utf-8")
    (repo / "src" / "app.py").write_text("import torch\nprint(torch.cuda.is_available())\n", encoding="utf-8")
    (repo / "requirements.txt").write_text("torch\n", encoding="utf-8")

    runtime = analyze_source(str(repo), output_dir=tmp_path / "runtime", scan_mode="runtime")
    full = analyze_source(str(repo), output_dir=tmp_path / "full", scan_mode="full")

    assert runtime.inventory.scan_scope == "Runtime deployment scan"
    assert full.inventory.scan_scope == "Full repository audit"
    assert not any(risk.file.startswith("docs/") for risk in runtime.risks)
    assert any(risk.file.startswith("docs/") for risk in full.risks)


def test_runtime_scan_includes_common_ai_app_directories(tmp_path):
    repo = tmp_path / "repo"
    (repo / "modules").mkdir(parents=True)
    (repo / "docker" / "docker-cuda").mkdir(parents=True)
    (repo / "modules" / "devices.py").write_text("import torch\nprint(torch.cuda.is_available())\n", encoding="utf-8")
    (repo / "docker" / "docker-cuda" / "README.md").write_text("CUDA_VISIBLE_DEVICES=0\n", encoding="utf-8")
    (repo / "requirements.txt").write_text("torch\n", encoding="utf-8")

    runtime = analyze_source(str(repo), output_dir=tmp_path / "runtime-ai-app", scan_mode="runtime")

    assert any(risk.file == "modules/devices.py" for risk in runtime.risks)
    assert not any(risk.file == "docker/docker-cuda/README.md" for risk in runtime.risks)


def test_scan_applies_file_limit_but_keeps_deployment_critical_files(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "requirements.txt").write_text("torch\nbitsandbytes\n", encoding="utf-8")
    (repo / "Dockerfile").write_text("FROM nvidia/cuda:12.1.0-runtime-ubuntu22.04\n", encoding="utf-8")
    (repo / "src").mkdir()
    for index in range(MAX_SCAN_FILES + 25):
        (repo / "src" / f"file_{index:04d}.py").write_text("print('ok')\n", encoding="utf-8")

    result = analyze_source(str(repo), output_dir=tmp_path / "limited", scan_mode="runtime")

    assert result.inventory.scan_limit_applied is True
    assert result.inventory.files_scanned == MAX_SCAN_FILES
    assert result.inventory.files_omitted_by_limit > 0
    assert any(risk.file == "requirements.txt" and risk.rule_id == "dep.bitsandbytes" for risk in result.risks)
    assert any(risk.file == "Dockerfile" and risk.rule_id == "docker.nvidia_cuda_base" for risk in result.risks)


def test_extensionless_root_readme_is_scanned(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "README").write_text("This demo mentions nvidia-smi in the root README.\n", encoding="utf-8")

    result = analyze_source(str(repo), output_dir=tmp_path / "readme", scan_mode="runtime")

    assert result.inventory.files_scanned == 1
    assert result.risks[0].file == "README"
