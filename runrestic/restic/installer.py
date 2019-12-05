import bz2
import json
import logging
import os
from shutil import which

import requests

logger = logging.getLogger(__name__)


def restic_check() -> bool:
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
