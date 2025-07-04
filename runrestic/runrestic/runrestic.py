"""
Runrestic main module.

This module serves as the entry point for the `runrestic` application. It handles
logging configuration, signal handling, and the execution of Restic operations
based on user-provided configuration files and command-line arguments.
"""

import logging
import os
import signal
import sys
from typing import Any

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
    """
    Configure logging for the application.

    Args:
        level (str): The logging level as a string (e.g., "info", "debug").
    """
    level = logging.getLevelName(level.upper())
    log = logging.getLogger("runrestic")
    log.setLevel(level)
    handler = logging.StreamHandler()
    handler.setLevel(level)
    formatter = logging.Formatter("%(message)s")
    handler.setFormatter(formatter)
    log.addHandler(handler)


def configure_signals() -> None:
    """
    Configure signal handling for the application.

    This function ensures that the application properly handles termination signals
    by killing the entire process group.
    """

    def kill_the_group(signal_number: signal.Signals, _frame: Any) -> None:
        """
        Kill the entire process group when a signal is received.

        Args:
            signal_number (signal.Signals): The signal received.
            _frame (Any): The current stack frame (unused).
        """
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
    """
    Main function for the `runrestic` application.

    This function checks for the Restic binary, parses command-line arguments,
    configures logging and signals, loads configuration files, and executes
    the specified Restic actions.
    """
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
            raise FileNotFoundError(f"Error: No configuration files found in {possible_config_paths()}")  # noqa: TRY003

    configs: list[dict[str, Any]] = []
    for config in config_file_paths:
        parsed_cfg = parse_configuration(config)
        if parsed_cfg:
            configs.append(parsed_cfg)

    if args.show_progress:
        os.environ["RESTIC_PROGRESS_FPS"] = str(1 / float(args.show_progress))

    if "shell" in args.actions:
        restic_shell(configs)
        return

    # Track the results (number of errors) per config
    result: list[int] = []
    for config in configs:
        runner = ResticRunner(config, args, extras)
        result.append(runner.run())

    if sum(result) > 0:
        sys.exit(1)


if __name__ == "__main__":
    runrestic()
