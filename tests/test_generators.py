from pathlib import Path

from mi300x_launch_doctor.benchmark.results import sample_benchmark
from mi300x_launch_doctor.generator.dockerfile import generate_dockerfile
from mi300x_launch_doctor.generator.requirements import generate_requirements
from mi300x_launch_doctor.generator.vllm_script import generate_vllm_script
from mi300x_launch_doctor.intake.inventory import iter_scannable_files


def test_generators_produce_rocm_vllm_content():
    root = Path("fixtures/cuda_risk_repo").resolve()
    files = iter_scannable_files(root)

    dockerfile = generate_dockerfile().content
    requirements = generate_requirements(root, files).content
    script = generate_vllm_script().content
    benchmark = sample_benchmark()

    assert "FROM rocm/pytorch:latest" in dockerfile
    assert "# bitsandbytes==0.43.1" in requirements
    assert "vllm/vllm-openai-rocm:latest" in script
    assert "--device=/dev/kfd" in script
    assert benchmark.status_label == "Sample / Expected Format"
