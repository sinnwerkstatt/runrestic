"""
This module provides functionality for parsing CLI arguments and reading configuration files.

It includes utilities to handle command-line arguments, locate configuration files, and parse
them into structured data. The module also validates configuration files against a predefined
JSON schema to ensure correctness.
"""

import json
import logging
import os
from argparse import ArgumentParser, Namespace
from importlib.resources import open_text
from typing import Any

import jsonschema
import toml

from runrestic import __version__
from runrestic.runrestic.tools import deep_update

logger = logging.getLogger(__name__)

CONFIG_DEFAULTS: dict[str, Any] = {
    "execution": {
        "parallel": False,
        "exit_on_error": True,
        "retry_count": 0,
    }
}
with open_text("runrestic.runrestic", "schema.json", encoding="utf-8") as schema_file:
    SCHEMA: dict[str, Any] = json.load(schema_file)


def cli_arguments(args: list[str] | None = None) -> tuple[Namespace, list[str]]:
    """
    Parse command-line arguments for the `runrestic` application.

    Args:
        args (list[str] | None): A list of arguments to parse. If None, uses `sys.argv`.

    Returns:
        tuple[Namespace, list[str]]: A tuple containing parsed options and extra arguments.
    """
    parser = ArgumentParser(
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
        help="one or more from the following actions: [shell, init, backup, prune, check, stats, unlock]",
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
        "--show-progress",
        metavar="INTERVAL",
        help="Updated interval in seconds for restic progress (default: None)",
    )
    parser.add_argument(
        "-v", "--version", action="version", version="%(prog)s " + __version__
    )

    options, extras = parser.parse_known_args(args)
    if extras:
        extras = [x for x in extras if x != "--"]
    else:
        valid_actions = [
            "shell",
            "init",
            "backup",
            "forget",
            "prune",
            "check",
            "stats",
            "unlock",
        ]
        extras = []
        new_actions: list[str] = []
        for act in options.actions:
            if act in valid_actions:
                new_actions += [act]
            else:
                extras += [act]
        options.actions = new_actions
    return options, extras


def possible_config_paths() -> list[str]:
    """
    Generate a list of possible configuration file paths.

    Returns:
        list[str]: A list of paths where configuration files might be located.
    """
    user_config_directory = os.getenv("XDG_CONFIG_HOME") or os.path.expandvars(
        os.path.join("$HOME", ".config")
    )
    return [
        "/etc/runrestic.toml",
        "/etc/runrestic.json",
        "/etc/runrestic/",
        f"{user_config_directory}/runrestic/",
    ]


def configuration_file_paths() -> list[str]:
    """
    Locate readable configuration files from possible paths.

    Returns:
        list[str]: A list of valid configuration file paths.
    """
    paths: list[str] = []
    for path in possible_config_paths():
        path = os.path.realpath(path)
        # Check access permission, includes check for path existence
        if not os.access(path, os.R_OK):
            logger.debug("No access to path %s skipping", path)
            continue

        if os.path.isfile(path):
            paths += [path]
            continue

        for filename in os.listdir(path):
            filename = os.path.join(path, filename)
            if (
                filename.endswith(".toml") or filename.endswith(".json")
            ) and os.path.isfile(filename):
                octal_permissions = oct(os.stat(filename).st_mode)
                if octal_permissions[-2:] != "00":  # file permissions are too broad
                    logger.warning(
                        "NOT using %s.\n"
                        "File permissions are too open (%s). "
                        "You should set it to 0600: `chmod 0600 %s`\n",
                        filename,
                        octal_permissions[-4:],
                        filename,
                    )
                    continue

                paths += [filename]

    return paths


def parse_configuration(config_filename: str) -> dict[str, Any]:
    """
    Parse a configuration file and validate it against the schema.

    Args:
        config_filename (str): The path to the configuration file.

    Returns:
        dict[str, Any]: The parsed and validated configuration as a dictionary.
    """
    logger.debug("Parsing configuration file: %s", config_filename)
    with open(config_filename, encoding="utf-8") as file:
        config: dict[str, Any] = (
            toml.load(file)
            if str(config_filename).endswith(".toml")
            else json.load(file)
        )
    config = deep_update(CONFIG_DEFAULTS, dict(config))

    if "name" not in config:
        config["name"] = os.path.basename(config_filename)

    jsonschema.validate(instance=config, schema=SCHEMA)
    return config
