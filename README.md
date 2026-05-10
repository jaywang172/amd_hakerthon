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
  - qwen
  - qwen3.5
  - qwen3.5-0.8b
  - gradio
  - ai-agents
  - mlops
---

# MI300X Launch Doctor

**AI-powered ROCm deployment readiness for AMD MI300X.**

MI300X Launch Doctor is a deployment readiness and MLOps automation system for teams moving AI workloads to AMD ROCm and AMD Instinct MI300X. Paste a GitHub repository, scan a local folder, or upload project files, and the system produces a ROCm readiness score, prioritized deployment blockers, AMD-ready deployment files, and an optional Qwen3.5/vLLM benchmark report.

It is **not** a CUDA-to-ROCm translator. Instead, it answers the deployment question teams ask before migration:

> Can this AI workload run on AMD, what must change, and how do we validate it?

## Live Demo

- **Hugging Face Space:** https://huggingface.co/spaces/jay171/mi300x-launch-doctor
- **Live app:** https://jay171-mi300x-launch-doctor.hf.space/
- **GitHub repository:** https://github.com/jaywang172/mi300x-launch-doctor

## Why This Exists

Many AI projects are CUDA-first even when they are not intentionally NVIDIA-only. Migration risk is often spread across:

- CUDA Docker base images
- Python device calls such as `torch.cuda` and `.cuda()`
- CUDA-oriented dependencies such as `bitsandbytes`, `flash-attn`, `cupy-cuda`, and `tensorflow-gpu`
- CI workflows and shell commands such as `nvidia-smi`
- inference scripts that assume a specific GPU runtime
- documentation and examples that hide deployment assumptions

Before deploying to AMD Developer Cloud or MI300X, engineering teams need a fast way to identify the blockers, generate a starting deployment pack, and produce a report they can share with infra teams or leadership.

MI300X Launch Doctor turns that uncertainty into a concrete deployment readiness report.

## What It Does

- Scans public GitHub repositories, local folders, uploaded zip files, or selected project files.
- Detects AMD ROCm compatibility risks across dependencies, Dockerfiles, Python code, native CUDA code, CI/runtime configuration, and inference setup.
- Generates a 0-100 ROCm readiness score.
- Separates high-priority deployment blockers from lower-priority audit context.
- Produces AMD-ready generated files:
  - `AMD_DEPLOYMENT_REPORT.md`
  - `Dockerfile.rocm`
  - `requirements-rocm.txt`
  - `run_vllm_amd.sh`
  - `scan_result.json`
- Uses `Qwen/Qwen3.5-0.8B` as the default benchmark target model for generated AMD ROCm/vLLM validation scripts.
- Accepts real benchmark JSON when available, while clearly labeling demo benchmark output as sample data.

## Demo Story

The recommended demo flow is:

1. Run the built-in CUDA-risk fixture.
2. Show the low ROCm readiness score and deployment blockers.
3. Open the generated AMD deployment pack.
4. Show the vLLM ROCm script using Qwen3.5 as the default MI300X validation target.
5. Run the mostly-ready fixture.
6. Show that the scanner can also produce a high readiness score.
7. Optionally scan a real public GitHub repository to prove repo intake works.

Recommended demo inputs:

| Input | Purpose | Expected Result |
| --- | --- | --- |
| `fixtures/cuda_risk_repo` | Shows CUDA-first deployment risk | `19/100`, 10 findings, clear blockers |
| `fixtures/mostly_ready_repo` | Shows a mostly portable PyTorch-style app | `100/100`, small number of recommendations |
| `https://github.com/gradio-app/gradio` | Real medium-size public repo | Successful runtime scan |
| `https://github.com/huggingface/transformers` | Large AI framework stress test | Successful scan, but not recommended as the main demo |

## Quick Start

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the Gradio app:

```bash
python app.py
```

The app runs on port `7860` by default:

```text
http://localhost:7860
```

Use a different port:

```bash
GRADIO_SERVER_PORT=7861 python app.py
```

Run the CLI scanner:

```bash
python scan_repo.py fixtures/cuda_risk_repo --out generated/cuda_risk
python scan_repo.py fixtures/mostly_ready_repo --out generated/mostly_ready
python scan_repo.py https://github.com/gradio-app/gradio --scan-mode runtime --out generated/gradio_runtime
```

Run a full audit instead of the default runtime scan:

```bash
python scan_repo.py https://github.com/huggingface/transformers --scan-mode full --out generated/transformers_full
```

## Inputs

MI300X Launch Doctor supports:

- public GitHub repository URLs
- GitHub URLs with `.git`, trailing slashes, `tree/...`, `blob/...`, or query strings
- local folder paths
- uploaded zip files
- uploaded individual files
- optional benchmark JSON

GitHub intake first tries:

```text
git clone --depth 1
```

If clone fails, it falls back to GitHub zipball download.

Malformed URLs and unsupported sources return clear UI errors instead of stack traces.

## Scan Modes

### Runtime Deployment Scan

This is the default mode and the best choice for demos.

It focuses on files that are likely to affect deployment:

- dependency files
- Dockerfiles and Docker Compose files
- app/server/inference entrypoints
- runtime source directories
- CI workflow risks
- root README context

It reduces noise from docs, examples, tests, and tutorials so the result feels closer to an actual deployment-readiness check.

### Full Repository Audit

This mode scans all scannable files in scope.

Use it for:

- migration discovery
- stress testing
- internal engineering review
- finding CUDA assumptions in docs, examples, tests, and CI

## Risk Detection

The static scanner is deterministic and rule-based. It intentionally avoids live model dependencies so the public demo stays fast and reliable.

Current risk categories include:

| Category | Examples |
| --- | --- |
| Docker base image | `nvidia/cuda` |
| Docker runtime | `--gpus all` |
| CUDA APIs | `torch.cuda`, `.cuda()` |
| Hardcoded device config | `CUDA_VISIBLE_DEVICES` |
| CUDA-specific commands | `nvidia-smi` |
| Quantization risk | `bitsandbytes` |
| Attention/kernel risk | `flash-attn`, `xformers`, `triton` |
| CUDA-specific packages | `cupy-cuda`, `tensorflow-gpu` |
| Native CUDA | `cudaMalloc`, `cudaMemcpy`, CUDA kernel launch syntax |
| Inference engine validation | `vllm` |

Example risk item:

```json
{
  "severity": "high",
  "category": "dependency",
  "file": "requirements.txt",
  "line": 4,
  "evidence": "flash-attn==2.5.0",
  "why_it_matters": "flash-attn uses specialized attention kernels that must be validated for ROCm compatibility.",
  "recommendation": "Validate ROCm-compatible attention kernels or use the serving image's supported attention backend."
}
```

## Readiness Score

The readiness score starts at `100` and applies risk penalties:

| Severity | Penalty |
| --- | --- |
| High | `-15` |
| Medium | `-8` |
| Low | `-3` |

The same rule is capped so repeated instances of one pattern do not completely dominate the score.

The scorer also adds small readiness bonuses for useful deployment signals:

- Dockerfile or Docker Compose present
- dependency metadata present
- PyTorch detected
- inference/serving entrypoint detected
- no high-severity CUDA-only dependency found

Labels:

| Score | Label |
| --- | --- |
| `85-100` | Ready for AMD deployment |
| `70-84` | Mostly ready |
| `50-69` | Needs migration work |
| `0-49` | High migration risk |

## Generated Deployment Pack

Every successful scan can generate:

```text
AMD_DEPLOYMENT_REPORT.md
Dockerfile.rocm
requirements-rocm.txt
run_vllm_amd.sh
scan_result.json
```

### Dockerfile.rocm

The generated Dockerfile starts from:

```dockerfile
FROM rocm/pytorch:latest
```

This gives teams a practical ROCm/PyTorch starting point while reminding production users to pin tested ROCm versions.

### requirements-rocm.txt

The generated requirements file preserves safe dependencies and comments CUDA-specific packages with migration notes.

Example:

```text
# bitsandbytes==0.43.1
# ROCm note: Validate ROCm quantization support or replace backend.
```

### run_vllm_amd.sh

The generated script follows the ROCm inference path with a ROCm-enabled vLLM Docker image:

```bash
MODEL_ID="${MODEL_ID:-Qwen/Qwen3.5-0.8B}"
MAX_MODEL_LEN="${MAX_MODEL_LEN:-32768}"
PORT="${PORT:-8000}"

docker run --rm -it \
  --device=/dev/kfd \
  --device=/dev/dri \
  --group-add video \
  --ipc=host \
  --shm-size 8G \
  -p "${PORT}:8000" \
  vllm/vllm-openai-rocm:latest \
  vllm serve "${MODEL_ID}" \
  --dtype bfloat16 \
  --max-model-len "${MAX_MODEL_LEN}" \
  --language-model-only \
  --host 0.0.0.0 \
  --port 8000
```

## Qwen Integration

MI300X Launch Doctor uses:

```text
Qwen/Qwen3.5-0.8B
```

as the default benchmark target model for generated AMD ROCm deployment scripts.

Qwen3.5-0.8B is small enough for fast prototyping while still fitting modern serving stacks such as:

- vLLM
- SGLang
- KTransformers
- Hugging Face Transformers

The scanner does **not** depend on live Qwen inference. That is deliberate: the public demo remains stable and fast, while Qwen is used as the default target for MI300X/vLLM deployment validation.

The generated vLLM command uses:

```bash
MAX_MODEL_LEN=32768
```

as a conservative default for demo stability. Users can raise this value when memory budget allows.

## Benchmark Handling

The benchmark section is honest by design.

If no real benchmark JSON is supplied, the report shows:

```text
Benchmark Status: Sample / Expected Format
```

If real benchmark JSON is uploaded, the report shows:

```text
Benchmark Status: Real Run
```

Example benchmark JSON:

```json
{
  "benchmark_mode": "real",
  "model": "Qwen/Qwen3.5-0.8B",
  "backend": "vLLM ROCm",
  "gpu": "AMD Instinct MI300X",
  "load_success": true,
  "avg_latency_ms": 742,
  "p50_latency_ms": 690,
  "p95_latency_ms": 1103,
  "tokens_per_second": 68.4,
  "memory_used_gb": 18.2
}
```

## Stress-Test Behavior

MI300X Launch Doctor is hardened for small, medium, and large repositories.

Stress safeguards:

- skips `.git`, caches, virtualenvs, `node_modules`, build folders, generated output, model checkpoints, and common artifact directories
- ignores individual text files larger than 1 MB
- caps each scan at 3000 prioritized files
- prioritizes deployment-critical files when limits are applied
- bounds inventory text used for framework detection
- separates audit context from runtime deployment blockers
- keeps the UI focused on the top 10 deployment blockers
- stores full structured output in `scan_result.json`

Generated reports include:

```text
Files discovered in scope
Files scanned
Files omitted by stress limit
```

Tested cases:

| Case | Result |
| --- | --- |
| `fixtures/cuda_risk_repo` | `19/100`, high-risk deployment blockers |
| `fixtures/mostly_ready_repo` | `100/100`, mostly portable app path |
| `gradio-app/gradio` | medium public repo scan succeeds |
| `huggingface/transformers` | large AI framework runtime scan succeeds |
| malformed URL | clear error, no stack trace |
| GitHub `tree/...` URL | accepted and scanned |
| extensionless root `README` | scanned correctly |

## Architecture

```text
User
  |
  v
Gradio / Hugging Face Space UI
  |
  v
Repo Intake
  - local path
  - uploaded files
  - GitHub clone
  - GitHub zipball fallback
  |
  v
File Inventory and Scan Scope
  - Runtime deployment scan
  - Full repository audit
  - stress limits
  |
  v
Static ROCm Compatibility Scanner
  - Docker rules
  - dependency rules
  - Python GPU rules
  - native CUDA rules
  |
  v
Readiness Scoring
  |
  v
Deployment Pack Generator
  - Dockerfile.rocm
  - requirements-rocm.txt
  - run_vllm_amd.sh
  |
  v
Markdown and JSON Reports
```

## Project Structure

```text
.
├── app.py
├── scan_repo.py
├── requirements.txt
├── mi300x_launch_doctor/
│   ├── benchmark/
│   ├── generator/
│   ├── intake/
│   ├── report/
│   ├── scanner/
│   ├── scoring/
│   ├── pipeline.py
│   └── schemas.py
├── fixtures/
│   ├── cuda_risk_repo/
│   ├── mostly_ready_repo/
│   └── rocm_ready_repo/
└── tests/
```

## CLI Reference

Scan a local fixture:

```bash
python scan_repo.py fixtures/cuda_risk_repo --out generated/cuda_risk
```

Scan a public GitHub repository:

```bash
python scan_repo.py https://github.com/gradio-app/gradio --scan-mode runtime --out generated/gradio
```

Run a full audit:

```bash
python scan_repo.py https://github.com/huggingface/transformers --scan-mode full --out generated/transformers_full
```

Use a real benchmark JSON:

```bash
python scan_repo.py fixtures/mostly_ready_repo \
  --benchmark-json benchmark.json \
  --out generated/real_benchmark
```

## Testing

Run all tests:

```bash
python -m pytest
```

The test suite covers:

- scanner rule detection
- readiness scoring
- runtime vs full scan modes
- stress scan limits
- report generation
- benchmark mode switching
- UI bad-input behavior
- generated ROCm/vLLM file contents

Latest local verification:

```text
18 passed
```

## Hackathon Positioning

MI300X Launch Doctor is designed for the AMD Developer Hackathon as an AI agentic workflow for deployment readiness:

```text
Repository -> Scan -> Score -> Fix Pack -> Qwen3.5/vLLM Validation Target -> Report
```

It targets:

- AI startup founders evaluating AMD deployment
- MLOps engineers checking ROCm readiness
- enterprise AI infra teams planning CUDA-to-AMD migration
- hackathon builders trying to get Hugging Face or GitHub AI projects running on AMD Developer Cloud

## Tech Stack

- Python
- Gradio
- Hugging Face Spaces
- AMD ROCm
- AMD Instinct MI300X
- vLLM
- Qwen/Qwen3.5-0.8B
- PyTorch
- Docker
- GitHub

## Known Scope Boundaries

The project intentionally does not attempt:

- full CUDA C++ to HIP translation
- private repo OAuth
- automatic pull request creation
- live MI300X benchmarking from the public Space UI
- enterprise auth or billing
- fine-tuning
- distributed training

These are future extensions. The MVP focuses on a complete, reliable deployment-readiness loop that can run in a public demo.

## Submission Links

- **GitHub:** https://github.com/jaywang172/mi300x-launch-doctor
- **Hugging Face Space:** https://huggingface.co/spaces/jay171/mi300x-launch-doctor
- **Live app:** https://jay171-mi300x-launch-doctor.hf.space/

## License

This hackathon project is intended as an open-source developer tool. Add a repository license file before production reuse if required by your organization.
