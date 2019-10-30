import logging
import os
import signal

from runrestic.config.configuration import (
    cli_arguments,
    configuration_file_paths,
    parse_configuration,
    possible_config_paths,
)
from runrestic.restic.runner import ResticRunner
from runrestic.restic.shell import restic_shell

logger = logging.getLogger(__name__)


def configure_logging(level: str):
    level = logging.getLevelName(level.upper())
    log = logging.getLogger("runrestic")
    log.setLevel(level)
    handler = logging.StreamHandler()
    handler.setLevel(level)
    formatter = logging.Formatter("%(message)s")
    handler.setFormatter(formatter)
    log.addHandler(handler)


def configure_signals():
    def kill_the_group(signal_number, frame):
        os.killpg(os.getpgrp(), signal_number)

    signals = [
        signal.SIGINT,
        signal.SIGHUP,
        signal.SIGTERM,
        signal.SIGUSR1,
        signal.SIGUSR2,
    ]

    [signal.signal(sig, kill_the_group) for sig in signals]


def main():
    args = cli_arguments()
    configure_logging(args.log_level)
    configure_signals()

    if args.config_file:
        config_file_paths = [args.config_file]
    else:
        config_file_paths = list(configuration_file_paths())

        if not len(config_file_paths):
            raise FileNotFoundError(
                f"Error: No configuration files found in {possible_config_paths()}"
            )

    configs = [parse_configuration(c) for c in config_file_paths]

    if "shell" in args.actions:
        return restic_shell(configs)

    for config in configs:
        runner = ResticRunner(config, args)
        runner.run()
        print(runner.times)


if __name__ == "__main__":
    main()
