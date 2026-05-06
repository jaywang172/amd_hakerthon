from __future__ import annotations

from pathlib import Path

from mi300x_launch_doctor.schemas import RepoInventory


TEXT_EXTENSIONS = {
    ".py",
    ".cu",
    ".cpp",
    ".cc",
    ".cxx",
    ".c",
    ".h",
    ".hpp",
    ".txt",
    ".md",
    ".toml",
    ".cfg",
    ".ini",
    ".yaml",
    ".yml",
    ".json",
    ".sh",
    ".dockerfile",
}

IMPORTANT_NAMES = {
    "requirements.txt",
    "requirements-dev.txt",
    "pyproject.toml",
    "setup.py",
    "setup.cfg",
    "dockerfile",
    "docker-compose.yml",
    "docker-compose.yaml",
    "readme.md",
    "app.py",
    "main.py",
    "serve.py",
    "inference.py",
    "generate.py",
}

SKIP_DIRS = {
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".venv",
    "venv",
    "env",
    "node_modules",
    "dist",
    "build",
    "generated",
    "models",
    "checkpoints",
}

MAX_FILE_BYTES = 1_000_000


def iter_scannable_files(root: Path) -> list[Path]:
    if root.is_file():
        return [root] if is_scannable_file(root) else []
    files: list[Path] = []
    for path in root.rglob("*"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.is_file() and is_scannable_file(path):
            files.append(path)
    return sorted(files)


def filter_runtime_files(root: Path, files: list[Path]) -> list[Path]:
    runtime_files = [path for path in files if is_runtime_deployment_file(path, root)]
    return runtime_files or files


def is_runtime_deployment_file(path: Path, root: Path) -> bool:
    rel = safe_relative(path, root)
    parts = rel.lower().split("/")
    name = Path(rel).name.lower()
    if parts[0] in {"docs", "doc", "documentation", "site"}:
        return False
    if parts[0] == "examples":
        return False
    if ".github" in parts:
        return len(parts) >= 3 and parts[0] == ".github" and parts[1] == "workflows"
    if parts[0] in {"src", "app", "server", "mi300x_launch_doctor"}:
        return True
    if name in IMPORTANT_NAMES:
        return True
    if name.startswith("dockerfile"):
        return True
    if name in {"server.py", "main.py", "inference.py", "serve.py", "app.py", "generate.py"}:
        return True
    if len(parts) == 1 and path.suffix.lower() in {".py", ".toml", ".txt", ".yaml", ".yml", ".sh"}:
        return True
    return False


def is_scannable_file(path: Path) -> bool:
    name = path.name.lower()
    if name in IMPORTANT_NAMES or name.startswith("dockerfile"):
        return True
    if path.suffix.lower() not in TEXT_EXTENSIONS:
        return False
    try:
        return path.stat().st_size <= MAX_FILE_BYTES
    except OSError:
        return False


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def build_inventory(root: Path, source: str, repo_name: str, files: list[Path], scan_scope: str = "Full repository audit") -> RepoInventory:
    rels = [safe_relative(path, root) for path in files]
    rel_names = {rel.lower() for rel in rels}
    important = [rel for rel in rels if Path(rel).name.lower() in IMPORTANT_NAMES or Path(rel).name.lower().startswith("dockerfile")]
    all_text = "\n".join(read_text(path)[:200_000] for path in files)
    languages: list[str] = []
    frameworks: list[str] = []
    if any(rel.endswith(".py") for rel in rels):
        languages.append("Python")
    if any(rel.endswith((".cu", ".cpp", ".cc", ".cxx", ".h", ".hpp")) for rel in rels):
        languages.append("Native/CUDA/C++")
    if any("dockerfile" in Path(rel).name.lower() for rel in rels):
        languages.append("Docker")
    if "torch" in all_text or "pytorch" in all_text.lower():
        frameworks.append("PyTorch")
    if "transformers" in all_text.lower():
        frameworks.append("Transformers")
    if "vllm" in all_text.lower():
        frameworks.append("vLLM")
    if "gradio" in all_text.lower():
        frameworks.append("Gradio")
    has_dockerfile = any("dockerfile" in Path(rel).name.lower() for rel in rels)
    has_requirements = bool(rel_names.intersection({"requirements.txt", "pyproject.toml", "setup.py", "setup.cfg"}))
    uses_pytorch = "PyTorch" in frameworks
    has_inference_script = any(
        Path(rel).name.lower() in {"serve.py", "inference.py", "generate.py", "run_inference.py"}
        or "vllm" in rel.lower()
        for rel in rels
    )
    return RepoInventory(
        repo_name=repo_name,
        source=source,
        root_path=str(root),
        scan_scope=scan_scope,
        files_scanned=len(files),
        important_files=important[:50],
        languages=languages,
        frameworks=frameworks,
        has_dockerfile=has_dockerfile,
        has_requirements=has_requirements,
        uses_pytorch=uses_pytorch,
        has_inference_script=has_inference_script,
    )


def safe_relative(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.name
