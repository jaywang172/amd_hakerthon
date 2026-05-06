from pathlib import Path

from mi300x_launch_doctor.intake.inventory import build_inventory, iter_scannable_files
from mi300x_launch_doctor.scanner.scan_files import scan_files
from mi300x_launch_doctor.scoring.readiness import score_readiness


def test_score_labels_and_caps_repeated_rule_penalties():
    root = Path("fixtures/cuda_risk_repo").resolve()
    files = iter_scannable_files(root)
    inventory = build_inventory(root, str(root), root.name, files)
    risks = scan_files(root, files)
    score = score_readiness(inventory, risks)

    assert 0 <= score.score <= 100
    assert score.label in {"Mostly ready", "Needs migration work", "High migration risk", "Ready for AMD deployment"}


def test_mostly_ready_fixture_scores_high():
    root = Path("fixtures/mostly_ready_repo").resolve()
    files = iter_scannable_files(root)
    inventory = build_inventory(root, str(root), root.name, files)
    risks = scan_files(root, files)
    score = score_readiness(inventory, risks)

    assert score.score >= 85


def test_spread_runtime_cuda_risks_reduce_score_below_perfect(tmp_path):
    repo = tmp_path / "repo"
    (repo / "modules").mkdir(parents=True)
    for index in range(4):
        (repo / "modules" / f"gpu_{index}.py").write_text("import torch\nprint(torch.cuda.is_available())\n", encoding="utf-8")
    (repo / "requirements.txt").write_text("torch\n", encoding="utf-8")

    files = iter_scannable_files(repo)
    inventory = build_inventory(repo, str(repo), repo.name, files)
    risks = scan_files(repo, files)
    score = score_readiness(inventory, risks)

    assert score.score < 100
