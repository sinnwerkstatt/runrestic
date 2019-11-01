import argparse
import json
import logging
import os

import jsonschema
import pkg_resources
import toml

from runrestic import __version__
from runrestic.runrestic.tools import deep_update

logger = logging.getLogger(__name__)

CONFIG_DEFAULTS = {"execution": {"parallel": False, "exit_on_error": True}}
SCHEMA = json.load(
    open(pkg_resources.resource_filename("runrestic", "runrestic/schema.json"), "r")
)


def cli_arguments(args: list = None):
    parser = argparse.ArgumentParser(
        prog="runrestic",
        description="""
            A wrapper for restic. It runs restic based on config files and also outputs metrics.
            To initialize the repos, run `runrestic init`.
            If you don't define any actions, it will default to `backup prune check`, and `stats` if metrics are set.
            """,
    )
    parser.add_argument(
        "actions",
        type=str,
        nargs="*",
        help="one or more from the following actions: [init,backup,prune,check]",
    )
    parser.add_argument(
        "-n",
        "--dry-run",
        dest="dry_run",
        action="store_true",
        help="Apply --dry-run where applicable (i.e.: forget)",
    )
    parser.add_argument(
        "-l",
        "--log-level",
        metavar="LOG_LEVEL",
        dest="log_level",
        default="info",
        help="Choose from: critical, error, warning, info, debug. (default: info)",
    )
    parser.add_argument(
        "-c",
        "--config",
        dest="config_file",
        help="Use an alternative configuration file",
    )
    parser.add_argument(
        "-v", "--version", action="version", version="%(prog)s " + __version__
    )
    return parser.parse_args(args)


def possible_config_paths():
    user_config_directory = os.getenv("XDG_CONFIG_HOME") or os.path.expandvars(
        os.path.join("$HOME", ".config")
    )
    return [
        "/etc/runrestic.toml",
        "/etc/runrestic",
        f"{user_config_directory}/runrestic",
    ]


def configuration_file_paths():
    for path in possible_config_paths():
        path = os.path.realpath(path)

        if not os.path.exists(path):
            continue

        if not os.path.isdir(path):  # pragma: no cover
            yield path
            continue

        for filename in os.listdir(path):
            filename = os.path.join(path, filename)
            if filename.endswith(".toml") and not os.path.isdir(filename):
                octal_permissions = oct(os.stat(filename).st_mode)
                if octal_permissions[-2:] != "00":  # file permissions are too broad
                    logger.warning(
                        (
                            f"NOT using {filename}.\n"
                            f"File permissions are too open ({octal_permissions[-4:]}). "
                            f"You should set it to 0600: `chmod 0600 {filename}`\n"
                        )
                    )
                else:
                    yield filename


def parse_configuration(config_filename):
    logger.debug(f"Parsing configuration file: {config_filename}")
    with open(config_filename) as file:
        try:
            config = toml.load(file)
        except toml.TomlDecodeError as e:
            logger.warning(f"Problem parsing {config_filename}: {e}\n")
            return

    config = deep_update(CONFIG_DEFAULTS, config)

    if "name" not in config:
        config["name"] = os.path.basename(config_filename)

    jsonschema.validate(instance=config, schema=SCHEMA)
    return config
