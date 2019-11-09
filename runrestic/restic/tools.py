import logging
import os
import time
from multiprocessing.pool import ApplyResult, Pool
from subprocess import PIPE, Popen, STDOUT
from typing import Dict

from runrestic.runrestic.tools import parse_time

logger = logging.getLogger(__name__)


def retry_process(cmd, config: dict = None):
    start_time = time.time()

    shell = config.get("shell", False)
    tries_total = config["retry_count"] + 1
    status = {"tries_total": tries_total, "output": []}

    for i in range(0, tries_total):
        status["current_try"] = i + 1
        p = Popen(cmd, stdout=PIPE, stderr=STDOUT, shell=shell)
        p.wait()
        status["output"] += [(p.returncode, p.stdout.read().decode("UTF-8"))]

        if p.returncode == 0:
            break

        if config.get("retry_backoff"):
            if " " in config["retry_backoff"]:
                duration, strategy = config["retry_backoff"].split(" ")
            else:
                duration, strategy = config["retry_backoff"], None
            duration = parse_time(duration)

            if strategy == "linear":
                time.sleep(duration * (i + 1))
            elif strategy == "exponential":
                time.sleep(duration << i)
            else:  # strategy = "static"
                time.sleep(duration)

    status["time"] = time.time() - start_time
    return status


def run_multiple_commands(commands: list, config: dict) -> Dict[str, dict]:
    concurrent_processes = len(commands) if config["parallel"] else 1
    pool = Pool(processes=concurrent_processes)

    i = 0
    threads: Dict[str, ApplyResult] = {}
    for command in commands:
        if isinstance(command, tuple):
            cmd_id = command[0]
            cmd = command[1]
        else:
            cmd_id = i
            i += 1
            cmd = command

        logger.debug(f'Spawning "{cmd}"')
        threads[cmd_id] = pool.apply_async(retry_process, (cmd, config))

    retval = {cmd_id: process.get() for cmd_id, process in threads.items()}
    return retval


def initialize_environment(config: dict):
    for key, value in config.items():
        logger.debug(f"[Environment] {key}={value}")
        os.environ[key] = value

    if not (os.environ.get("HOME") or os.environ.get("XDG_CACHE_HOME")):
        os.environ["XDG_CACHE_HOME"] = "/var/cache"
