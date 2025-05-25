"""
This module provides functionality to check for the presence of the Restic binary
on the system and to download and install it if necessary.

It interacts with the GitHub API to fetch the latest Restic release and handles
the installation process, including permissions and alternative paths.
"""

import bz2
import json
import logging
from pathlib import Path
from shutil import which

import requests

logger = logging.getLogger(__name__)


def restic_check() -> bool:
    """
    Check if the Restic binary is available on the system.

    If Restic is not found, the user is prompted to install it.

    Returns:
        bool: True if Restic is available or successfully installed, False otherwise.
    """
    if which("restic"):
        return True
    carry_on = input(
        "There seems to be no restic on your system. Should I install it now? [Y/n] "
    )
    if carry_on in ["", "y", "Y"]:
        download_restic()
        return True
    return False


def download_restic() -> None:
    """
    Download and install the latest Restic binary.

    The function fetches the latest release information from the Restic GitHub repository,
    downloads the compressed binary, decompresses it, and installs it to `/usr/local/bin/restic`.
    If permissions are insufficient, the user is prompted to provide an alternative path.
    """
    try:
        response = requests.get(
            "https://api.github.com/repos/restic/restic/releases/latest", timeout=10
        )
        response.raise_for_status()
        github_json = json.loads(response.content)
    except requests.exceptions.Timeout:
        print("Error: Unable to fetch the latest Restic release due to a timeout.")
        return
    except requests.exceptions.RequestException as e:
        print(f"Error: Unable to fetch the latest Restic release: {e}")
        return

    download_url = ""
    for asset in github_json.get("assets", []):
        if "linux_amd64.bz2" in asset["name"]:
            download_url = asset["browser_download_url"]
            break

    if not download_url:
        print("Error: Could not find a suitable Restic binary to download.")
        return

    try:
        file = requests.get(download_url, allow_redirects=True, timeout=60).content
    except requests.exceptions.Timeout:
        print("Error: Unable to download the Restic binary due to a timeout.")
        return
    except requests.exceptions.RequestException as e:
        print(f"Error: Unable to download the Restic binary: {e}")
        return

    program = bz2.decompress(file)
    try:
        path = Path("/usr/local/bin/restic")
        path.write_bytes(program)

        path.chmod(0o755)
    except PermissionError as e:
        print(e)
        print("\nTry re-running this as root.")
        print("Alternatively you can specify a path where I can put restic.")
        alt_path = input("Example: /home/you/.bin/restic. Leave blank to exit.\n")
        if alt_path:
            path = Path(alt_path)
            path.write_bytes(program)
            path.chmod(0o755)
