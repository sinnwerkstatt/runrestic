"""
This module provides functionality to interact with Restic repositories via a shell.

It allows users to select a repository from a list of available configurations and spawns
a new shell with the appropriate environment variables set for Restic operations.
"""

import logging
import os
import pty
import sys
from typing import Any

from runrestic.restic.tools import initialize_environment

logger = logging.getLogger(__name__)


def restic_shell(configs: list[dict[str, Any]]) -> None:
    """
    Launch a shell with environment variables set for a selected Restic repository.

    If only one repository is available, it is automatically selected. Otherwise, the user
    is prompted to choose a repository from the available configurations.

    Args:
        configs (list[dict[str, Any]]): A list of configuration dictionaries, each containing
            repository information and environment variables.

    Raises:
        ValueError: If the user provides an invalid selection index.
    """
    if len(configs) == 1 and len(configs[0]["repositories"]) == 1:
        logger.info("Found only one repository, using that one:\n")
        selected_config = configs[0]
        selected_repo = configs[0]["repositories"][0]
    else:
        print("The following repositories are available:")
        all_repos: list[tuple[dict[str, Any], str]] = []
        i = 0
        for config in configs:
            for repo in config["repositories"]:
                print(f"[{i}] - {config['name']}:{repo}")
                all_repos.append((config, repo))
                i += 1

        try:
            selection = int(input(f"Choose a repo [0-{i - 1}]: "))
            selected_config, selected_repo = all_repos[selection]
        except (ValueError, IndexError):
            raise ValueError("Invalid selection. Please choose a valid repository index.")  # noqa: B904, TRY003

    env: dict[str, str] = selected_config["environment"]
    env.update({"RESTIC_REPOSITORY": selected_repo})

    print(f"Using: \033[1;92m{selected_config['name']}:{selected_repo}\033[0m")
    print("Spawning a new shell with the restic environment variables all set.")
    initialize_environment(env)
    print("\nTry `restic snapshots` for example.")
    pty.spawn(os.environ["SHELL"])
    print("You've exited your restic shell.")
    sys.exit(0)
