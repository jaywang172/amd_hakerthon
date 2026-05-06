from pathlib import Path

from mi300x_launch_doctor.intake.inventory import iter_scannable_files
from mi300x_launch_doctor.scanner.scan_files import scan_files


def test_scanner_detects_cuda_dependency_docker_and_python_risks():
    root = Path("fixtures/cuda_risk_repo").resolve()
    risks = scan_files(root, iter_scannable_files(root))
    rule_ids = {risk.rule_id for risk in risks}

    assert "docker.nvidia_cuda_base" in rule_ids
    assert "system.nvidia_smi" in rule_ids
    assert "env.cuda_visible_devices" in rule_ids
    assert "python.torch_cuda" in rule_ids
    assert "python.cuda_method" in rule_ids
    assert "dep.bitsandbytes" in rule_ids
    assert "dep.flash_attn" in rule_ids


def test_vllm_dependency_is_reported_once_per_file(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "setup.py").write_text("vllm\nvllm\nvllm\n", encoding="utf-8")

    risks = scan_files(repo, iter_scannable_files(repo))

    assert [risk.rule_id for risk in risks].count("dep.vllm") == 1
