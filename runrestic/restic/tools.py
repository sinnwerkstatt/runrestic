import logging
import os
import time
from concurrent.futures import Future
from concurrent.futures.process import ProcessPoolExecutor
from subprocess import PIPE, Popen, STDOUT
from typing import Any, Dict, List, Optional, Sequence, Union

from runrestic.runrestic.tools import parse_time

logger = logging.getLogger(__name__)


class MultiCommand:
    def __init__(
        self,
        commands: Sequence[Union[List[str], str]],
        config: Dict[str, Any],
        abort_reasons: Optional[List[str]] = None,
    ):
        self.processes: List[Future[Dict[str, Any]]] = []
        self.commands = commands
        self.config = config
        self.abort_reasons = abort_reasons
        self.process_pool_executor = ProcessPoolExecutor(
            max_workers=len(commands) if config["parallel"] else 1
        )

    def run(self) -> List[Dict[str, Any]]:
        for command in self.commands:
            logger.debug(f'Spawning "{command}"')
            process = self.process_pool_executor.submit(
                retry_process, command, self.config, self.abort_reasons
            )
            self.processes += [process]

        # result() is blocking. The function will return when all processes are done
        return [process.result() for process in self.processes]


def retry_process(
    cmd: List[str], config: Dict[str, Any], abort_reasons: Optional[List[str]] = None
) -> Dict[str, Any]:
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


def initialize_environment(config: Dict[str, Any]) -> None:
    for key, value in config.items():
        os.environ[key] = value
        if key == "RESTIC_PASSWORD":
            value = "**********"
        logger.debug(f"[Environment] {key}={value}")

    if os.geteuid() == 0:  # pragma: no cover; if user is root, we just use system cache
        os.environ["XDG_CACHE_HOME"] = "/var/cache"
    elif not (os.environ.get("HOME") or os.environ.get("XDG_CACHE_HOME")):
        os.environ["XDG_CACHE_HOME"] = "/var/cache"
