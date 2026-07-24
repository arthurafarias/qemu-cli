import hashlib
import os
import subprocess
from typing import Optional

from .config import GIT_CACHE_DIR
from .debug_log import trace
from .errors import QemuCLIError


@trace
def fetch_descriptor(url: str, path: str, ref: Optional[str] = None) -> str:
    """Shallow-clone (or update) `url` into the git cache and return the
    text content of `path` inside the checked-out tree."""
    repo_dir = os.path.join(GIT_CACHE_DIR, hashlib.sha256(url.encode()).hexdigest()[:16])
    _sync_repo(url, repo_dir, ref)
    file_path = os.path.join(repo_dir, path)
    if not os.path.isfile(file_path):
        raise QemuCLIError(f"no such file in repo: {path}")
    with open(file_path) as fh:
        return fh.read()


def _sync_repo(url: str, repo_dir: str, ref: Optional[str]) -> None:
    if os.path.isdir(os.path.join(repo_dir, ".git")):
        _run(["git", "-C", repo_dir, "fetch", "--depth", "1", "origin", ref or "HEAD"])
        _run(["git", "-C", repo_dir, "checkout", "FETCH_HEAD"])
        return
    os.makedirs(GIT_CACHE_DIR, exist_ok=True)
    cmd = ["git", "clone", "--depth", "1"]
    if ref:
        cmd += ["--branch", ref]
    cmd += [url, repo_dir]
    _run(cmd)


def _run(argv) -> None:
    try:
        result = subprocess.run(argv, capture_output=True, text=True)
    except FileNotFoundError as e:
        raise QemuCLIError("git not found; install git to use 'vm pull'") from e
    if result.returncode != 0:
        raise QemuCLIError(f"git failed: {result.stderr.strip()}")
