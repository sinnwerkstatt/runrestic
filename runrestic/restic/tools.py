import logging
import os
import subprocess
from typing import List, Tuple, Any, Dict

from runrestic.runrestic.tools import Timer

logger = logging.getLogger(__name__)


def run_multiple_commands(commands: list, config: dict = None) -> dict:
    if not config:
        config = {}
    shell = config.get("shell", False)

    processes: Dict[str, Any] = {}

    i = 0
    for command in commands:
        if isinstance(command, tuple):
            cmd_id = command[0]
            cmd = command[1]
        else:
            cmd_id = i
            cmd = command

        logger.debug(f'Spawning "{cmd}"')
        timer = Timer()
        p = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=shell
        )

        if not config["parallel"]:
            p.wait()
            timer.stop()
        processes[cmd_id] = {"process": p, "timer": timer}
        i += 1

    for cmd_id, p_infos in processes.items():
        p = p_infos["process"]
        if config["parallel"]:
            p.wait()
            p_infos["timer"].stop()

        p_infos["returncode"] = p.returncode
        p_infos["output"] = p.stdout.read().decode("UTF-8")

    return processes


def initialize_environment(config: dict):
    for key, value in config.items():
        logger.debug(f"[Environment] {key}={value}")
        os.environ[key] = value

    if not (os.environ.get("HOME") or os.environ.get("XDG_CACHE_HOME")):
        os.environ["XDG_CACHE_HOME"] = "/var/cache"
