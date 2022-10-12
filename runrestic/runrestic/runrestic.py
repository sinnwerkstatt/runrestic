"""Runrestic main module"""
import logging
import os
import signal
import sys
from typing import Any, Dict, List

from runrestic.restic.installer import restic_check
from runrestic.restic.runner import ResticRunner
from runrestic.restic.shell import restic_shell
from runrestic.runrestic.configuration import (
    cli_arguments,
    configuration_file_paths,
    parse_configuration,
    possible_config_paths,
)

logger = logging.getLogger(__name__)


def configure_logging(level: str) -> None:
    level = logging.getLevelName(level.upper())
    log = logging.getLogger("runrestic")
    log.setLevel(level)
    handler = logging.StreamHandler()
    handler.setLevel(level)
    formatter = logging.Formatter("%(message)s")
    handler.setFormatter(formatter)
    log.addHandler(handler)


def configure_signals() -> None:
    def kill_the_group(signal_number: signal.Signals, _frame: Any) -> None:
        os.killpg(os.getpgrp(), signal_number)

    signals = [
        signal.SIGINT,
        signal.SIGHUP,
        signal.SIGTERM,
        signal.SIGUSR1,
        signal.SIGUSR2,
    ]

    _ = [signal.signal(sig, kill_the_group) for sig in signals]  # type: ignore[arg-type]


def runrestic() -> None:
    if not restic_check():
        return

    args, extras = cli_arguments()
    configure_logging(args.log_level)
    configure_signals()

    if args.config_file:
        config_file_paths = [args.config_file]
    else:
        config_file_paths = list(configuration_file_paths())

        if not config_file_paths:
            raise FileNotFoundError(
                f"Error: No configuration files found in {possible_config_paths()}"
            )

    configs: List[Dict[str, Any]] = []
    for config in config_file_paths:
        parsed_cfg = parse_configuration(config)
        if parsed_cfg:
            configs += [parsed_cfg]
    if args.show_progress:
        os.environ["RESTIC_PROGRESS_FPS"] = str(1 / float(args.show_progress))

    if "shell" in args.actions:
        restic_shell(configs)
        return

    # Track the results (number of errors) per config
    result: List[int] = []
    for config in configs:
        runner = ResticRunner(config, args, extras)
        result.append(runner.run())

    if sum(result) > 0:
        sys.exit(1)


if __name__ == "__main__":
    runrestic()
