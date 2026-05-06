from __future__ import annotations

from collections import Counter, defaultdict

from mi300x_launch_doctor.schemas import RepoInventory, RiskItem, ScoreResult


SEVERITY_PENALTIES = {
    "high": 15,
    "medium": 8,
    "low": 3,
}

MAX_PENALTIES_PER_RULE = 2


def score_readiness(inventory: RepoInventory, risks: list[RiskItem]) -> ScoreResult:
    score = 100
    penalty_counts: dict[str, int] = defaultdict(int)
    penalty_summary: Counter[str] = Counter()

    for risk in risks:
        rule_key = risk.rule_id or f"{risk.category}:{risk.severity}"
        if penalty_counts[rule_key] >= MAX_PENALTIES_PER_RULE:
            continue
        penalty_counts[rule_key] += 1
        penalty = SEVERITY_PENALTIES[risk.severity]
        score -= penalty
        penalty_summary[f"{risk.severity}:{risk.category}"] += penalty

    bonus_reasons: list[str] = []
    if inventory.has_dockerfile:
        score += 5
        bonus_reasons.append("Repository includes a Dockerfile or Docker Compose file.")
    if inventory.has_requirements:
        score += 5
        bonus_reasons.append("Repository includes dependency metadata.")
    if inventory.uses_pytorch:
        score += 5
        bonus_reasons.append("Repository appears to use PyTorch, which has an established ROCm path.")
    if inventory.has_inference_script:
        score += 5
        bonus_reasons.append("Repository includes an inference or serving entrypoint.")
    if not any(risk.category in {"dependency", "quantization"} and risk.severity == "high" for risk in risks):
        score += 5
        bonus_reasons.append("No high-severity CUDA-only dependency was detected.")

    score = max(0, min(100, score))
    return ScoreResult(
        score=score,
        label=label_for_score(score),
        bonus_reasons=bonus_reasons,
        penalty_summary=dict(sorted(penalty_summary.items())),
    )


def label_for_score(score: int) -> str:
    if score >= 85:
        return "Ready for AMD deployment"
    if score >= 70:
        return "Mostly ready"
    if score >= 50:
        return "Needs migration work"
    return "High migration risk"
