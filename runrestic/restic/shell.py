import logging
import os
import pty
import sys
from typing import Any, Dict, List, Tuple

from runrestic.restic.tools import initialize_environment

logger = logging.getLogger(__name__)


def restic_shell(configs: List[Dict[str, Any]]) -> None:
    if len(configs) == 1 and len(configs[0]["repositories"]) == 1:
        logger.info("Found only one repository, using that one:\n")
        selected_config = configs[0]
        selected_repo = configs[0]["repositories"][0]
    else:
        print("The following repositories are available:")
        all_repos: List[Tuple[Dict[str, Any], str]] = []
        i = 0
        for config in configs:
            for repo in config["repositories"]:
                print(f"[{i}] - {config['name']}:{repo}")
                all_repos += [(config, repo)]
                i += 1

        selection = int(input(f"Choose a repo [0-{i - 1}]: "))
        selected_config, selected_repo = all_repos[selection]

    env = selected_config["environment"]
    env.update({"RESTIC_REPOSITORY": selected_repo})

    print(f"Using: \033[1;92m{selected_config['name']}:{selected_repo}\033[0m")
    print("Spawning a new shell with the restic environment variables all set.")
    initialize_environment(env)
    print("\nTry `restic snapshots` for example.")
    pty.spawn(os.environ["SHELL"])
    print("You've exited your restic shell.")
    sys.exit(0)
