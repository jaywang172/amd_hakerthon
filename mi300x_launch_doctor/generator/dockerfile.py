from __future__ import annotations

from mi300x_launch_doctor.schemas import GeneratedFile, ScanResult


def generate_dockerfile(result: ScanResult | None = None) -> GeneratedFile:
    content = """FROM rocm/pytorch:latest

# MI300X Launch Doctor generated this ROCm-ready starting point.
# For production, pin a tested ROCm/PyTorch image tag instead of latest.

WORKDIR /workspace

COPY requirements-rocm.txt .
RUN pip install --upgrade pip && pip install -r requirements-rocm.txt

COPY . .

CMD ["python", "app.py"]
"""
    return GeneratedFile(name="Dockerfile.rocm", path="generated/Dockerfile.rocm", content=content)
