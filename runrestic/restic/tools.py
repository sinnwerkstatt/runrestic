import logging
import os
import re
import time
from concurrent.futures import Future
from concurrent.futures.process import ProcessPoolExecutor
from subprocess import PIPE, STDOUT, Popen
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
            logger.debug("Spawning %s", command)
            process = self.process_pool_executor.submit(
                retry_process, command, self.config, self.abort_reasons
            )
            self.processes += [process]

        # result() is blocking. The function will return when all processes are done
        return [process.result() for process in self.processes]


def log_messages(process: Any, proc_cmd: str) -> str:
    """Capture the process output and generate appropriate log messages

    Parameters
    ----------
    process : Popen[str]  # this typing only works for Python >= 3.9
        Subprocess instance
    proc_cmd : str
        Name of the executed command (as it should appear in the logs)

    Returns
    -------
    str
        Complete process output
    """
    output = ""
    for log_out in process.stdout:
        if log_out.strip():
            output += log_out
            if re.match(r"^critical|fatal", log_out, re.I):
                proc_log_level = logging.CRITICAL
            elif re.match(r"^error", log_out, re.I):
                proc_log_level = logging.ERROR
            elif re.match(r"^warning", log_out, re.I):
                proc_log_level = logging.WARNING
            elif re.match(
                r"^unchanged\s+/", log_out, re.I
            ):  # unchanged files in restic output
                proc_log_level = logging.DEBUG
            else:
                proc_log_level = logging.INFO
            logger.log(proc_log_level, "[%s] %s", proc_cmd, log_out.strip())
    return output


def retry_process(
    cmd: Union[str, List[str]],
    config: Dict[str, Any],
    abort_reasons: Optional[List[str]] = None,
) -> Dict[str, Any]:
    start_time = time.time()

    shell = config.get("shell", False)
    tries_total = config.get("retry_count", 0) + 1
    status = {"current_try": 0, "tries_total": tries_total, "output": []}
    if isinstance(cmd, list):
        proc_cmd = cmd[0]
    else:
        proc_cmd = os.path.basename(cmd.split(" ", maxsplit=1)[0])
    for i in range(0, tries_total):
        status["current_try"] = i + 1

        with Popen(
            cmd, stdout=PIPE, stderr=STDOUT, shell=shell, encoding="UTF-8"
        ) as process:
            output = log_messages(process, proc_cmd)
        returncode = process.returncode
        status["output"] += [(returncode, output)]
        if returncode == 0:
            break

        if abort_reasons and any(
            [abort_reason in output for abort_reason in abort_reasons]
        ):
            logger.error(
                "Aborting '%s' because of %s",
                proc_cmd,
                [
                    abort_reason
                    for abort_reason in abort_reasons
                    if abort_reason in output
                ],
            )
            break
        if config.get("retry_backoff"):
            if " " in config["retry_backoff"]:
                duration, strategy = config["retry_backoff"].split(" ")
            else:
                duration, strategy = config["retry_backoff"], None
            duration = parse_time(duration)
            logger.info(
                "Retry %s/%s command '%s' using %s strategy, duration = %s sec",
                i + 1,
                tries_total,
                proc_cmd,
                strategy,
                duration,
            )

            if strategy == "linear":
                time.sleep(duration * (i + 1))
            elif strategy == "exponential":
                time.sleep(duration << i)
            else:  # strategy = "static"
                time.sleep(duration)
        else:
            logger.info(
                "Retry %s/%s command '%s'",
                i + 1,
                tries_total,
                proc_cmd,
            )

    status["time"] = time.time() - start_time
    return status


def initialize_environment(config: Dict[str, Any]) -> None:
    for key, value in config.items():
        os.environ[key] = value
        if key == "RESTIC_PASSWORD":
            value = "**********"
        logger.debug("[Environment] %s=%s", key, value)

    if os.geteuid() == 0:  # pragma: no cover; if user is root, we just use system cache
        os.environ["XDG_CACHE_HOME"] = "/var/cache"
    elif not (os.environ.get("HOME") or os.environ.get("XDG_CACHE_HOME")):
        os.environ["XDG_CACHE_HOME"] = "/var/cache"


def redact_password(repo_str: str, pw_replacement: str) -> str:
    re_repo = re.compile(r"(^(?:[s]?ftp:|rest:http[s]?:|s3:http[s]?:).*?):(\S+)(@.*$)")
    return (
        re_repo.sub(rf"\1:{pw_replacement}\3", repo_str)
        if pw_replacement
        else re_repo.sub(r"\1\3", repo_str)
    )
