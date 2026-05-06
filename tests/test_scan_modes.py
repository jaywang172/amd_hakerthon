from pathlib import Path

from mi300x_launch_doctor.pipeline import analyze_source


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
