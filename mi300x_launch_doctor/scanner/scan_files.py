from __future__ import annotations

from pathlib import Path

from mi300x_launch_doctor.intake.inventory import read_text, safe_relative
from mi300x_launch_doctor.scanner.rules import RULES
from mi300x_launch_doctor.schemas import RiskItem


def scan_files(root: Path, files: list[Path]) -> list[RiskItem]:
    risks: list[RiskItem] = []
    for path in files:
        rel_path = safe_relative(path, root)
        text = read_text(path)
        risks.extend(scan_text(rel_path, text))
    return risks


def scan_text(rel_path: str, text: str) -> list[RiskItem]:
    risks: list[RiskItem] = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        for rule in RULES:
            if not rule.applies_to(rel_path):
                continue
            if rule.pattern.search(stripped):
                risks.append(
                    RiskItem(
                        severity=rule.severity,
                        category=rule.category,
                        file=rel_path,
                        line=line_no,
                        evidence=compact_evidence(stripped),
                        why_it_matters=rule.why_it_matters,
                        recommendation=rule.recommendation,
                        rule_id=rule.rule_id,
                    )
                )
    return risks


def compact_evidence(text: str, limit: int = 180) -> str:
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."
