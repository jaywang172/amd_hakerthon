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
    "readme",
    "readme.md",
    "app.py",
    "main.py",
    "webui.py",
    "launch.py",
    "server.py",
    "serve.py",
    "inference.py",
    "generate.py",
    "run_inference.py",
}

RUNTIME_CODE_DIRS = {
    "src",
    "app",
    "server",
    "modules",
    "comfy",
    "comfy_extras",
    "ldm",
    "extensions",
    "llamafactory",
    "mi300x_launch_doctor",
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
MAX_SCAN_FILES = 3_000
MAX_INVENTORY_TEXT_BYTES = 5_000_000
MAX_INVENTORY_BYTES_PER_FILE = 25_000


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


def limit_scannable_files(root: Path, files: list[Path], max_files: int = MAX_SCAN_FILES) -> tuple[list[Path], int]:
    if len(files) <= max_files:
        return sorted(files), 0
    prioritized = sorted(files, key=lambda path: file_priority(path, root))
    selected = sorted(prioritized[:max_files])
    return selected, len(files) - len(selected)


def file_priority(path: Path, root: Path) -> tuple[int, str]:
    rel = safe_relative(path, root)
    parts = rel.lower().split("/")
    name = Path(rel).name.lower()
    if name in {"requirements.txt", "pyproject.toml", "setup.py", "setup.cfg"}:
        return 0, rel
    if name.startswith("dockerfile") or name in {"docker-compose.yml", "docker-compose.yaml"}:
        return 1, rel
    if name in {"app.py", "main.py", "server.py", "serve.py", "inference.py", "generate.py", "run_inference.py", "webui.py", "launch.py"}:
        return 2, rel
    if parts[0] in RUNTIME_CODE_DIRS:
        return 3, rel
    if parts[0] == ".github":
        return 4, rel
    if name in {"readme", "readme.md"} and len(parts) == 1:
        return 5, rel
    return 9, rel


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
    if parts[0] in RUNTIME_CODE_DIRS:
        return True
    if name in {"readme", "readme.md"}:
        return len(parts) == 1
    if name in IMPORTANT_NAMES:
        return True
    if name.startswith("dockerfile"):
        return True
    if name in {"server.py", "main.py", "webui.py", "launch.py", "inference.py", "serve.py", "app.py", "generate.py", "run_inference.py"}:
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


def build_inventory(
    root: Path,
    source: str,
    repo_name: str,
    files: list[Path],
    scan_scope: str = "Full repository audit",
    files_discovered: int | None = None,
    files_omitted_by_limit: int = 0,
) -> RepoInventory:
    rels = [safe_relative(path, root) for path in files]
    rel_names = {rel.lower() for rel in rels}
    important = [rel for rel in rels if Path(rel).name.lower() in IMPORTANT_NAMES or Path(rel).name.lower().startswith("dockerfile")]
    all_text = bounded_inventory_text(files)
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
        files_discovered=files_discovered if files_discovered is not None else len(files),
        files_omitted_by_limit=files_omitted_by_limit,
        scan_limit_applied=files_omitted_by_limit > 0,
        important_files=important[:50],
        languages=languages,
        frameworks=frameworks,
        has_dockerfile=has_dockerfile,
        has_requirements=has_requirements,
        uses_pytorch=uses_pytorch,
        has_inference_script=has_inference_script,
    )


def bounded_inventory_text(files: list[Path]) -> str:
    chunks: list[str] = []
    total = 0
    for path in files:
        if total >= MAX_INVENTORY_TEXT_BYTES:
            break
        text = read_text(path)[:MAX_INVENTORY_BYTES_PER_FILE]
        remaining = MAX_INVENTORY_TEXT_BYTES - total
        if len(text) > remaining:
            text = text[:remaining]
        chunks.append(text)
        total += len(text)
    return "\n".join(chunks)


def safe_relative(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.name
