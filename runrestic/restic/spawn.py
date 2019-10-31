import logging
import subprocess
from typing import List, Tuple

logger = logging.getLogger(__name__)


def run_multiple_commands(
    commands: List[Tuple[str, list]], config: dict = None
) -> List[Tuple[str, int, str]]:
    if not config:
        config = {}
    shell = config.get("shell", False)

    processes = {}
    for cmd_id, cmd in commands:
        logger.debug(f'Spawning "{cmd}"')
        p = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=shell
        )
        if not config.get("parallel"):
            p.wait()
        processes[cmd_id] = p

    if config.get("parallel"):
        [process.wait() for process in processes.values()]

    return [
        (cmd_id, p.returncode, p.stdout.read().decode("UTF-8"))
        for cmd_id, p in processes.items()
    ]
