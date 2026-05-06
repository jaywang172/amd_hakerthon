---
title: MI300X Launch Doctor
emoji: 🩺
colorFrom: red
colorTo: yellow
sdk: gradio
sdk_version: 6.14.0
app_file: app.py
pinned: false
tags:
  - amd
  - amd-hackathon-2026
  - rocm
  - mi300x
  - vllm
  - gradio
  - ai-agents
  - mlops
---

# MI300X Launch Doctor

MI300X Launch Doctor is an AI deployment readiness system for AMD ROCm and MI300X. Paste a GitHub repo, and it scans dependencies, Dockerfiles, Python GPU calls, and inference setup to produce a ROCm readiness score, risk report, generated deployment files, and optional vLLM benchmark summary.

It is not a CUDA-to-ROCm translator. It is a deployment readiness and MLOps automation tool that helps teams answer: "Can this AI workload run on AMD, what must change, and how do we validate it?"

## What It Does

- Scans AI repositories and uploaded files
- Detects AMD ROCm compatibility risks
- Generates a ROCm readiness score
- Creates AMD deployment files
- Shows real benchmark JSON when provided, or a clearly labeled sample benchmark format

## Demo Flow

1. Paste a public GitHub repo URL, local path, or upload files.
2. Click Analyze.
3. Review the ROCm readiness score and risk table.
4. Open the generated `Dockerfile.rocm`, `requirements-rocm.txt`, `run_vllm_amd.sh`, and `AMD_DEPLOYMENT_REPORT.md`.
5. Replace sample benchmark data with real AMD Developer Cloud output when available.

## Quick Start

```bash
python scan_repo.py fixtures/cuda_risk_repo --out generated/cuda_risk
python scan_repo.py fixtures/mostly_ready_repo --out generated/mostly_ready
python scan_repo.py https://github.com/org/repo --scan-mode runtime --out generated/runtime_scan
python scan_repo.py https://github.com/org/repo --scan-mode full --out generated/full_audit
python app.py
```

The Gradio app runs on port `7860` by default. To use another port:

```bash
GRADIO_SERVER_PORT=7861 python app.py
```

## Example Cases

| Case | Purpose | Expected result |
| --- | --- | --- |
| `fixtures/cuda_risk_repo` | Shows a CUDA-first repo with obvious deployment risks | Low score, multiple high/medium findings |
| `fixtures/mostly_ready_repo` | Shows a mostly portable PyTorch-style repo | High score, small number of recommendations |
| Public GitHub repo URL | Shows real repo intake | Clone or zipball fallback, scan, report generation |

## Scan Modes

- `Runtime deployment scan`: default for demos and deployment readiness. It reduces docs/examples noise and focuses on dependency files, Docker files, serving entrypoints, runtime code, and CI workflow risks.
- `Full repository audit`: exhaustive scan across all scannable files, useful as a stress test or for full migration discovery.

## Generated Output

- `AMD_DEPLOYMENT_REPORT.md`
- `Dockerfile.rocm`
- `requirements-rocm.txt`
- `run_vllm_amd.sh`
- `scan_result.json`

## vLLM on ROCm Path

The generated vLLM script follows the ROCm inference path: using a ROCm-enabled vLLM Docker image, exposing AMD GPU devices, and serving an OpenAI-compatible endpoint for LLM inference on AMD Instinct GPUs.

`run_vllm_amd.sh` uses:

- `vllm/vllm-openai-rocm:latest`
- `/dev/kfd` and `/dev/dri`
- `--group-add video`
- `--ipc=host`
- `--shm-size 8G`
- `bfloat16`

## Benchmark Handling

The benchmark section is honest by design:

- `Benchmark Status: Real Run` means a real benchmark JSON file was supplied.
- `Benchmark Status: Sample / Expected Format` means the public demo is showing example output shape only.

## Tech Stack

- AMD ROCm
- AMD Instinct MI300X
- vLLM
- PyTorch
- Gradio
- Hugging Face Spaces

## Hackathon Note

Working deadline: May 11, 2026 03:00 Taipei time, pending final confirmation from the Event Schedule tab.
