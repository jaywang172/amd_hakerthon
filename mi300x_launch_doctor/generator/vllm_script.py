from __future__ import annotations

from mi300x_launch_doctor.schemas import GeneratedFile


def generate_vllm_script() -> GeneratedFile:
    content = """#!/usr/bin/env bash
set -euo pipefail

# Recommended inference path: vLLM on ROCm Docker
MODEL_ID="${MODEL_ID:-Qwen/Qwen2.5-0.5B-Instruct}"
PORT="${PORT:-8000}"

docker run --rm -it \\
  --device=/dev/kfd \\
  --device=/dev/dri \\
  --group-add video \\
  --ipc=host \\
  --shm-size 8G \\
  -p "${PORT}:8000" \\
  vllm/vllm-openai-rocm:latest \\
  --model "${MODEL_ID}" \\
  --dtype bfloat16 \\
  --host 0.0.0.0 \\
  --port 8000
"""
    return GeneratedFile(name="run_vllm_amd.sh", path="generated/run_vllm_amd.sh", content=content)
