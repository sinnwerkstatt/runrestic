import logging
import os
import sys
from argparse import ArgumentParser

import toml

from runrestic.config import collect, signals, log
from runrestic.config.environment import initialize_environment
from runrestic.metrics import generate_lines, write_lines
from runrestic.restic import ResticRepository
from runrestic import __version__

logger = logging.getLogger(__name__)


def parse_arguments():
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
    parser.add_argument('-l', '--log-level', metavar='LOG_LEVEL', dest='log_level', default='warning',
                        help='Choose from: critical, error, warning, info, debug. (default: warning)')
    parser.add_argument('-v', '--version', action='version', version='%(prog)s ' + __version__)
    args = parser.parse_args()
    return args


def run_configuration(config_filename, args):
    """
    Parse a single configuration file, and execute its defined backups, pruning, and/or consistency checks.
    """
    logger.info(f'Parsing configuration file: {config_filename}')
    with open(config_filename) as file:
        try:
            config = toml.load(file)
        except toml.TomlDecodeError as e:
            logger.warning(f"Problem parsing {config_filename}: {e}\n")
            return

    config['args'] = args

    if not args.action:
        args.action = ['backup', 'prune', 'check']

    initialize_environment(config.get('environment'))
    log_metrics = config.get('metrics') and not args.dry_run and not args.action == ['init']
    metrics_lines = ""

    for repository in config.get('repositories'):
        repo = ResticRepository(repository, log_metrics, args.dry_run)

        if 'init' in args.action:
            repo.init()
        if 'backup' in args.action:
            repo.backup(config.get('location'))
        if 'prune' in args.action:
            repo.forget(config.get('retention'))
            repo.prune()
        if 'check' in args.action:
            repo.check(config.get('consistency'))

        if log_metrics:
            config_name = config.get('config_name') or os.path.basename(config_filename)
            metrics_lines += generate_lines(repo.log, repository, config_name, config.get('metrics'))
    if log_metrics:
        write_lines(metrics_lines, config.get('metrics'))


def main():
    args = parse_arguments()
    signals.configure_signals()
    log.configure_logging(args.log_level)

    try:
        config_filenames = tuple(collect.collect_config_filenames())

        if len(config_filenames) == 0:
            raise ValueError('Error: No configuration files found in')

        for config_filename in config_filenames:
            run_configuration(config_filename, args)

    except (ValueError, OSError) as error:
        print(error)
        sys.exit(1)
