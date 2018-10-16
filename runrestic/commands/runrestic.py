import logging
import sys
from argparse import ArgumentParser

import toml

from runrestic.config import collect, signals, log
from runrestic.config.environment import initialize_environment
from runrestic.restic import ResticRepository

logger = logging.getLogger(__name__)


def parse_arguments(*arguments):
    """
    Given command-line arguments with which this script was invoked, parse the arguments and return
    them as an ArgumentParser instance.
    """
    config_paths = collect.get_default_config_paths()

    parser = ArgumentParser(
        prog='runrestic',
        description='''
            A wrapper for restic. It runs restic based on config files and also outputs metrics.
            If none of the --prune, --create, or --check options are given, then runrestic defaults
            to all three: prune, create, and check archives.
            '''
    )
    parser.add_argument('action', type=str, nargs='*',
                        help='one or more from the following actions: [init,backup,prune,check]')
    parser.add_argument('-n', '--dry-run', dest='dry_run', action='store_true',
                        help='Apply --dry-run where applicable (i.e.: forget)')
    args = parser.parse_args(arguments)
    return args


def run_configuration(config_filename, args):
    """
    Parse a single configuration file, and execute its defined pruning, backups, and/or consistency
    checks.
    """
    logger.info(f'Parsing configuration file: {config_filename}')
    with open(config_filename) as file:
        try:
            config = toml.load(file)
        except toml.TomlDecodeError as e:
            logger.warning(f"Problem parsing {config_filename}: {e}\n")
            return

    config['args'] = args

    initialize_environment(config.get('environment'))
    for repository in config.get('repositories'):
        repo = ResticRepository(repository, config)

        if 'init' in args.action:
            repo.init()
        if 'backup' in args.action:
            repo.backup()
        if 'prune' in args.action:
            repo.forget(prune=True)


    # try:
    #     local_path = location.get('local_path', 'borg')
    #     remote_path = location.get('remote_path')
    #     borg_create.initialize_environment(environment)
    #
    #     if metrics and not args.dry_run:
    #         stream = StringIO()
    #         stream_handler = logging.StreamHandler(stream)
    #         logging.getLogger('borg_output').addHandler(stream_handler)
    #         logging.getLogger('borg_output').setLevel(logging.INFO)
    #
    #     if args.create:
    #         hook.execute_hook(hooks.get('before_backup'), config_filename, 'pre-backup')
    #
    #     _run_commands(args, consistency, local_path, location, remote_path, retention, storage)
    #
    #     if args.create:
    #         hook.execute_hook(hooks.get('after_backup'), config_filename, 'post-backup')
    #
    #     if metrics and not args.dry_run:
    #         create_metrics(metrics)
    #
    # except (OSError, CalledProcessError):
    #     hook.execute_hook(hooks.get('on_error'), config_filename, 'on-error')
    #     raise


def main():
    args = parse_arguments(*sys.argv[1:])
    signals.configure_signals()
    log.configure_logging()

    try:
        config_filenames = tuple(collect.collect_config_filenames())

        if len(config_filenames) == 0:
            raise ValueError('Error: No configuration files found in')

        for config_filename in config_filenames:
            print(config_filename)
            run_configuration(config_filename, args)
    except (ValueError, OSError) as error:
        print(error)
        sys.exit(1)
