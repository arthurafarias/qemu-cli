import os
import shutil
import subprocess
from typing import Optional

from .debug_log import trace
from .errors import QemuCLIError


@trace
def download_image(uri: str, dest_dir: str, filename: Optional[str] = None) -> str:
    """Download a vm image via HTTP(S) or a magnet/torrent URI. Both
    transports go through aria2c, so no separate torrent library is needed."""
    if shutil.which("aria2c") is None:
        raise QemuCLIError("aria2c not found; install aria2 to download images")

    os.makedirs(dest_dir, exist_ok=True)
    cmd = ["aria2c", "-d", dest_dir, "--seed-time=0"]
    if filename:
        cmd += ["-o", filename]
    cmd.append(uri)

    result = subprocess.run(cmd)
    if result.returncode != 0:
        raise QemuCLIError(f"download failed (aria2c exit {result.returncode}): {uri}")

    return os.path.join(dest_dir, filename) if filename else dest_dir
