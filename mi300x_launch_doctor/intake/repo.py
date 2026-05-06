from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
import urllib.request
import zipfile
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse


GITHUB_RE = re.compile(r"^https?://github\.com/([^/\s]+)/([^/\s#?]+)")


@dataclass(frozen=True)
class PreparedSource:
    root: Path
    source_label: str
    cleanup_dir: Path | None = None


def prepare_source(source: str) -> PreparedSource:
    source = source.strip()
    if looks_like_url(source) and any(char.isspace() for char in source):
        raise ValueError(f"URL contains whitespace. Please provide a valid public GitHub repository URL: {source}")
    local_path = Path(source).expanduser()
    if local_path.exists():
        return PreparedSource(root=local_path.resolve(), source_label=str(local_path.resolve()))
    if is_github_url(source):
        return prepare_github_repo(source)
    raise ValueError(f"Unsupported source. Provide a local path or GitHub URL: {source}")


def prepare_uploaded_path(path: str) -> PreparedSource:
    uploaded = Path(path).expanduser().resolve()
    if uploaded.is_dir():
        return PreparedSource(root=uploaded, source_label=str(uploaded))
    if uploaded.suffix.lower() == ".zip":
        temp_dir = Path(tempfile.mkdtemp(prefix="mi300x-upload-"))
        root = extract_zip(uploaded, temp_dir)
        return PreparedSource(root=root, source_label=f"uploaded zip: {uploaded.name}", cleanup_dir=temp_dir)
    return PreparedSource(root=uploaded.parent, source_label=f"uploaded file: {uploaded.name}")


def is_github_url(source: str) -> bool:
    return bool(GITHUB_RE.match(source.strip()))


def looks_like_url(source: str) -> bool:
    return "://" in source


def github_repo_name(source: str) -> str:
    match = GITHUB_RE.match(source.strip())
    if not match:
        parsed = urlparse(source)
        return Path(parsed.path).name or Path(source).name
    owner, repo = match.groups()
    return f"{owner}/{repo.removesuffix('.git')}"


def prepare_github_repo(url: str) -> PreparedSource:
    temp_dir = Path(tempfile.mkdtemp(prefix="mi300x-repo-"))
    clone_dir = temp_dir / "repo"
    clone_error: Exception | None = None
    try:
        subprocess.run(
            ["git", "clone", "--depth", "1", url, str(clone_dir)],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=60,
        )
        return PreparedSource(root=clone_dir, source_label=url, cleanup_dir=temp_dir)
    except Exception as exc:
        clone_error = exc
        zip_path = temp_dir / "repo.zip"
        try:
            download_github_zipball(url, zip_path)
            root = extract_zip(zip_path, temp_dir / "unzipped")
            return PreparedSource(root=root, source_label=f"{url} (zipball fallback)", cleanup_dir=temp_dir)
        except Exception as zip_error:
            raise RuntimeError(
                "Could not clone or download this GitHub repository. "
                "Check that the repo exists, is public, and the URL points to a repository."
            ) from zip_error or clone_error


def download_github_zipball(url: str, target: Path) -> None:
    match = GITHUB_RE.match(url.strip())
    if not match:
        raise ValueError(f"Not a GitHub repository URL: {url}")
    owner, repo = match.groups()
    repo = repo.removesuffix(".git")
    zip_url = f"https://github.com/{owner}/{repo}/archive/refs/heads/main.zip"
    try:
        urllib.request.urlretrieve(zip_url, target)
        return
    except Exception:
        zip_url = f"https://github.com/{owner}/{repo}/archive/refs/heads/master.zip"
        urllib.request.urlretrieve(zip_url, target)


def extract_zip(zip_path: Path, destination: Path) -> Path:
    destination.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as archive:
        archive.extractall(destination)
    children = [child for child in destination.iterdir() if child.is_dir()]
    if len(children) == 1:
        return children[0]
    return destination


def cleanup_source(prepared: PreparedSource) -> None:
    if prepared.cleanup_dir and prepared.cleanup_dir.exists():
        shutil.rmtree(prepared.cleanup_dir, ignore_errors=True)
