import logging
import os
import sys
from argparse import ArgumentParser

import toml

from runrestic import __version__
from runrestic.commands import hooks
from runrestic.config import signals, log, validate
from runrestic.config.collect import get_default_config_paths, collect_config_filenames
from runrestic.config.environment import initialize_environment
from runrestic.metrics import generate_lines, write_lines
from runrestic.restic import ResticRepository

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
    parser.add_argument('-l', '--log-level', metavar='LOG_LEVEL', dest='log_level', default='info',
                        help='Choose from: critical, error, warning, info, debug. (default: info)')
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

    validate.validate_configuration(config)

    config['args'] = args

    if not args.action:
        args.action = ['backup', 'prune', 'check']

    initialize_environment(config.get('environment'))
    log_metrics = config.get('metrics') and not args.dry_run and not args.action == ['init']
    metrics_lines = ""

    rc = 0

    for repository in config.get('repositories'):
        logger.info(f"Repository: {repository}")
        repo = ResticRepository(repository, log_metrics, args.dry_run)

        if 'init' in args.action:
            rc += repo.init()
        elif not repo.check_initialization():
            logger.error(f"Repo {repository} is not initialized.\nHint: run `runrestic init`.")
            return

        if 'backup' in args.action:
            rc += hooks.execute_hook(config.get('backup'), 'pre_hook', repo)
            rc += repo.backup(config.get('backup'))
            rc += hooks.execute_hook(config.get('backup'), 'post_hook', repo)
        if 'prune' in args.action:
            rc += repo.forget(config.get('prune'))
            rc += repo.prune()
        if 'check' in args.action:
            rc += repo.check(config.get('check'))

        if log_metrics:
            config_name = config.get('config_name') or os.path.basename(config_filename)
            metrics_lines += generate_lines(repo.log, repository, config_name, config.get('metrics'))
    if log_metrics:
        write_lines(metrics_lines, config.get('metrics'))

    if rc > 0:
        logger.error('There were problems in this run. Add `-l debug` to get a more comprehensive output')

def main():
    args = parse_arguments()
    signals.configure_signals()
    log.configure_logging(args.log_level)

    try:
        config_filenames = tuple(collect_config_filenames())

        if len(config_filenames) == 0:
            raise ValueError(f'Error: No configuration files found in {get_default_config_paths()}')

        for config_filename in config_filenames:
            run_configuration(config_filename, args)

    except (ValueError, OSError) as error:
        print(error)
        sys.exit(1)
