"""
This module provides functionality to check for the presence of the Restic binary
on the system and to download and install it if necessary.

It interacts with the GitHub API to fetch the latest Restic release and handles
the installation process, including permissions and alternative paths.
"""

import bz2
import json
import logging
import os
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
    github_json = json.loads(
        requests.get(
            "https://api.github.com/repos/restic/restic/releases/latest"
        ).content
    )

    download_url = ""
    for asset in github_json["assets"]:
        if "linux_amd64.bz2" in asset["name"]:
            download_url = asset["browser_download_url"]
            break

    file = requests.get(download_url, allow_redirects=True).content

    program = bz2.decompress(file)
    try:
        path = "/usr/local/bin/restic"
        open(path, "wb").write(program)
        os.chmod(path, 0o755)
    except PermissionError as e:
        print(e)
        print("\nTry re-running this as root.")
        print("Alternatively you can specify a path where I can put restic.")
        alt_path = input("Example: /home/you/.bin/restic. Leave blank to exit.\n")
        if alt_path:
            open(alt_path, "wb").write(program)
            os.chmod(alt_path, 0o755)
