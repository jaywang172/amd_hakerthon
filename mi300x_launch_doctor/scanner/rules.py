from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Pattern

from mi300x_launch_doctor.schemas import Severity


@dataclass(frozen=True)
class ScanRule:
    rule_id: str
    pattern: Pattern[str]
    severity: Severity
    category: str
    why_it_matters: str
    recommendation: str
    file_hint: str = "any"

    def applies_to(self, rel_path: str) -> bool:
        lower = rel_path.lower()
        name = Path(lower).name
        if self.file_hint == "any":
            return True
        if self.file_hint == "docker":
            return "dockerfile" in name or name in {"docker-compose.yml", "docker-compose.yaml"}
        if self.file_hint == "python":
            return lower.endswith(".py")
        if self.file_hint == "dependency":
            return name in {"requirements.txt", "requirements-dev.txt", "pyproject.toml", "setup.py", "setup.cfg"}
        if self.file_hint == "native":
            return lower.endswith((".cu", ".cpp", ".cc", ".cxx", ".c", ".h", ".hpp"))
        return True


def regex(pattern: str) -> Pattern[str]:
    return re.compile(pattern, flags=re.IGNORECASE)


RULES: list[ScanRule] = [
    ScanRule(
        rule_id="docker.nvidia_cuda_base",
        pattern=regex(r"\bnvidia/cuda\b"),
        severity="high",
        category="docker_base_image",
        why_it_matters="NVIDIA CUDA base images do not provide an AMD ROCm runtime.",
        recommendation="Replace the base image with a ROCm-compatible image such as rocm/pytorch:latest, then pin a production ROCm version.",
        file_hint="docker",
    ),
    ScanRule(
        rule_id="docker.gpus_all",
        pattern=regex(r"--gpus\s+all"),
        severity="medium",
        category="docker_runtime",
        why_it_matters="The NVIDIA Docker runtime flag does not map to AMD GPU device access.",
        recommendation="Use ROCm Docker device flags: --device=/dev/kfd --device=/dev/dri --group-add video --ipc=host.",
        file_hint="docker",
    ),
    ScanRule(
        rule_id="system.nvidia_smi",
        pattern=regex(r"\bnvidia-smi\b"),
        severity="medium",
        category="system_command",
        why_it_matters="nvidia-smi is NVIDIA-specific and will not report AMD GPU status.",
        recommendation="Use rocm-smi or ROCm telemetry when running on AMD GPUs.",
    ),
    ScanRule(
        rule_id="env.cuda_visible_devices",
        pattern=regex(r"\bCUDA_VISIBLE_DEVICES\b"),
        severity="medium",
        category="hardcoded_device",
        why_it_matters="CUDA_VISIBLE_DEVICES is a CUDA-specific environment convention.",
        recommendation="Avoid hardcoding CUDA device environment variables; document AMD runtime device configuration separately.",
    ),
    ScanRule(
        rule_id="python.torch_cuda",
        pattern=regex(r"\btorch\.cuda\b"),
        severity="medium",
        category="cuda_api",
        why_it_matters="Direct torch.cuda calls can hardcode CUDA assumptions into device checks or memory logic.",
        recommendation="Use PyTorch device abstraction and validate behavior on ROCm where torch.cuda APIs may still exist but represent AMD GPUs.",
        file_hint="python",
    ),
    ScanRule(
        rule_id="python.cuda_method",
        pattern=regex(r"\.cuda\s*\("),
        severity="medium",
        category="cuda_api",
        why_it_matters="The .cuda() convenience call hardcodes CUDA-style device movement.",
        recommendation="Prefer .to(device) with device selected through configuration or runtime detection.",
        file_hint="python",
    ),
    ScanRule(
        rule_id="dep.bitsandbytes",
        pattern=regex(r"\bbitsandbytes\b"),
        severity="high",
        category="quantization",
        why_it_matters="bitsandbytes may assume CUDA-specific quantization backend paths.",
        recommendation="Validate ROCm support for the needed quantization mode or replace the quantization backend.",
        file_hint="dependency",
    ),
    ScanRule(
        rule_id="dep.flash_attn",
        pattern=regex(r"\bflash[-_]?attn\b"),
        severity="high",
        category="dependency",
        why_it_matters="flash-attn uses specialized attention kernels that must be validated for ROCm compatibility.",
        recommendation="Validate ROCm-compatible attention kernels or use the serving image's supported attention backend.",
        file_hint="dependency",
    ),
    ScanRule(
        rule_id="dep.xformers",
        pattern=regex(r"\bxformers\b"),
        severity="medium",
        category="dependency",
        why_it_matters="xFormers relies on optimized kernels that may vary by GPU backend.",
        recommendation="Check ROCm support for the exact xFormers version or disable unsupported kernels.",
        file_hint="dependency",
    ),
    ScanRule(
        rule_id="dep.triton",
        pattern=regex(r"\btriton\b"),
        severity="medium",
        category="dependency",
        why_it_matters="Triton kernel support should be validated against the ROCm stack and GPU target.",
        recommendation="Pin and test a ROCm-compatible Triton path, or rely on a prebuilt ROCm inference container.",
        file_hint="dependency",
    ),
    ScanRule(
        rule_id="dep.cupy_cuda",
        pattern=regex(r"\bcupy-cuda[0-9x]*\b"),
        severity="high",
        category="dependency",
        why_it_matters="cupy-cuda packages are built for CUDA-specific CuPy backends.",
        recommendation="Replace with a ROCm-compatible CuPy package or remove the CUDA-specific dependency.",
        file_hint="dependency",
    ),
    ScanRule(
        rule_id="dep.tensorflow_gpu",
        pattern=regex(r"\btensorflow-gpu\b"),
        severity="high",
        category="dependency",
        why_it_matters="tensorflow-gpu is a legacy CUDA-oriented TensorFlow package.",
        recommendation="Use a current TensorFlow path validated for ROCm or prefer PyTorch ROCm for this deployment.",
        file_hint="dependency",
    ),
    ScanRule(
        rule_id="dep.deepspeed",
        pattern=regex(r"\bdeepspeed\b"),
        severity="medium",
        category="dependency",
        why_it_matters="DeepSpeed custom ops may require ROCm-specific validation.",
        recommendation="Validate the exact DeepSpeed feature set on ROCm, especially custom ops and inference kernels.",
        file_hint="dependency",
    ),
    ScanRule(
        rule_id="dep.vllm",
        pattern=regex(r"\bvllm\b"),
        severity="low",
        category="inference_engine",
        why_it_matters="vLLM is a strong AMD inference target, but the deployment should use the ROCm-enabled image.",
        recommendation="Use vllm/vllm-openai-rocm for AMD inference and validate model support on MI300X.",
        file_hint="dependency",
    ),
    ScanRule(
        rule_id="native.cuda_file",
        pattern=regex(r"__global__|cudaMalloc|cudaMemcpy|cudaFree|<<<"),
        severity="high",
        category="native_cuda",
        why_it_matters="Native CUDA kernels or runtime APIs require manual ROCm/HIP migration work.",
        recommendation="Port CUDA C++ code to HIP or isolate it behind an optional backend with ROCm-compatible alternatives.",
        file_hint="native",
    ),
]
