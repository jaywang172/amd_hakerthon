from __future__ import annotations

import argparse
import sys
from pathlib import Path

from mi300x_launch_doctor.pipeline import analyze_source


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan an AI repo for AMD ROCm deployment readiness.")
    parser.add_argument("source", help="Public GitHub repo URL or local folder path.")
    parser.add_argument("--out", default="generated", help="Output directory for generated deployment files.")
    parser.add_argument("--benchmark-json", default=None, help="Optional real benchmark JSON file.")
    parser.add_argument(
        "--scan-mode",
        choices=["runtime", "full"],
        default="runtime",
        help="Use runtime deployment scan by default, or full repository audit for exhaustive findings.",
    )
    args = parser.parse_args()

    try:
        result = analyze_source(args.source, output_dir=args.out, benchmark_json=args.benchmark_json, scan_mode=args.scan_mode)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    output_dir = Path(args.out)
    severity_counts = {"high": 0, "medium": 0, "low": 0}
    for risk in result.risks:
        severity_counts[risk.severity] += 1

    print(f"Repo: {result.inventory.repo_name}")
    print(f"ROCm Readiness Score: {result.score.score}/100")
    print(f"Label: {result.score.label}")
    print(f"Scan scope: {result.inventory.scan_scope}")
    print(f"Risks: {len(result.risks)}")
    print(f"High risks: {severity_counts['high']}")
    print(f"Medium risks: {severity_counts['medium']}")
    print(f"Low risks: {severity_counts['low']}")
    print("Generated:")
    for name in ["AMD_DEPLOYMENT_REPORT.md", "Dockerfile.rocm", "requirements-rocm.txt", "run_vllm_amd.sh", "scan_result.json"]:
        print(f"- {output_dir / name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
