import os
import pty
import sys

from runrestic.config.environment import initialize_environment


def restic_shell(configs: list):
    print("The following repositories are available\n")
    i = 0
    all_repos = []
    for config in configs:
        print(config['name'])
        env = config.get('environment')
        for repo in config.get('repositories'):
            print("[{}] - {}".format(i, repo))
            all_repos += [(env, repo)]
            i += 1

    if i == 1:
        selection = 0
        print("Found only one repo.")
    else:
        selection = int(input("Choose a repo: "))

    env, repo = all_repos[selection]
    env.update({'RESTIC_REPOSITORY': repo})
    print("Using: {}".format(repo))
    print("Spawning a new shell with the restic environment variables all set.")
    print("Try `restic snapshots` for example.")
    initialize_environment(env)
    pty.spawn(os.environ.get('SHELL'))
    print("You've exited your restic shell.")
    sys.exit(0)
