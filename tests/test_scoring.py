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
