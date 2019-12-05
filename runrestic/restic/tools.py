import logging
import os
import time
from multiprocessing.pool import ApplyResult, Pool
from multiprocessing import Process
from subprocess import PIPE, Popen, STDOUT
from typing import Dict

from runrestic.runrestic.tools import parse_time

logger = logging.getLogger(__name__)


class MultiCommand:
    def __init__(self, commands: list, config: dict, abort_reasons: list = None):
        self.threads: Dict[str, ApplyResult] = {}
        self.commands = []
        i = 0
        for command in commands:
            if isinstance(command, tuple):
                self.commands += [command]
            else:
                self.commands += [(i, command)]
                i += 1
        self.config = config
        self.abort_reasons = abort_reasons
        concurrent_processes = len(commands) if config["parallel"] else 1
        self.pool = Pool(processes=concurrent_processes)

    def run(self) -> Dict[str, dict]:
        for command in self.commands:
            cmd_id, cmd = command
            logger.debug(f'Spawning "{cmd}"')
            self.threads[cmd_id] = self.pool.apply_async(
                retry_process, (cmd, self.config, self.abort_reasons)
            )
        return {cmd_id: process.get() for cmd_id, process in self.threads.items()}


def retry_process(cmd: list, config: dict = None, abort_reasons: list = None):
    start_time = time.time()

    shell = config.get("shell", False)
    tries_total = config.get("retry_count", 0) + 1
    status = {"current_try": 0, "tries_total": tries_total, "output": []}

    for i in range(0, tries_total):
        status["current_try"] = i + 1
        p = Popen(cmd, stdout=PIPE, stderr=STDOUT, shell=shell)
        p.wait()
        output = p.stdout.read().decode("UTF-8")
        status["output"] += [(p.returncode, output)]
        if p.returncode == 0:
            break

        if abort_reasons and any(
            [abort_reason in output for abort_reason in abort_reasons]
        ):
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


def initialize_environment(config: dict):
    for key, value in config.items():
        logger.debug(f"[Environment] {key}={value}")
        os.environ[key] = value

    if os.geteuid() == 0:  # if user is root, we just use system cache
        os.environ["XDG_CACHE_HOME"] = "/var/cache"
    elif not (os.environ.get("HOME") or os.environ.get("XDG_CACHE_HOME")):
        os.environ["XDG_CACHE_HOME"] = "/var/cache"
