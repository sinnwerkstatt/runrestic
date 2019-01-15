import logging
import os
import sys
import time
from argparse import ArgumentParser
from datetime import datetime

import toml

from runrestic import __version__
from runrestic.config import signals, log, validate
from runrestic.config.collect import get_default_config_paths, collect_config_filenames
from runrestic.config.environment import initialize_environment
from runrestic.metrics import write_lines
from runrestic.restic import ResticRepository
from runrestic.runrestic import hooks
from runrestic.runrestic.restic_shell import restic_shell
from runrestic.runrestic.tools import ReturnCodes

logger = logging.getLogger(__name__)


def parse_arguments():
    parser = ArgumentParser(
        prog='runrestic',
        description='''
            A wrapper for restic. It runs restic based on config files and also outputs metrics.
            To initialize a repo, run `runrestic init`.
            If you don't define an action, it will default to `backup prune check`, and `stats` if metrics are set.
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


def parse_configuration(config_filename):
    logger.info('Parsing configuration file: {config_filename}'.format(config_filename=config_filename))
    with open(config_filename) as file:
        try:
            config = toml.load(file)
        except toml.TomlDecodeError as e:
            logger.warning("Problem parsing {config_filename}: {e}\n".format(config_filename=config_filename, e=e))
            return

    validate.validate_configuration(config)
    if 'name' not in config:
        config['name'] = os.path.basename(config_filename)
    if 'exit_on_error' not in config:
        config['exit_on_error'] = True
    return config


def run_configuration(config, args):
    config['args'] = args
    total_time = time.time()

    initialize_environment(config.get('environment'))
    log_metrics = config.get('metrics') and not args.dry_run and not args.action == ['init']

    if not args.action and log_metrics:
        args.action = ['backup', 'prune', 'check', 'stats']
    elif not args.action:
        args.action = ['backup', 'prune', 'check']

    rcs = ReturnCodes(config['exit_on_error'])

    logs = {'repositories': {}}

    if 'backup' in args.action and config.get('backup').get('pre_hooks'):
        logs['restic_pre_hooks'] = hooks.execute_hook(config, 'pre_hooks')

    for repository in config.get('repositories'):
        logger.info("Repository: {repository}".format(repository=repository))
        repo = ResticRepository(repository, log_metrics, args.dry_run)

        if 'init' in args.action:
            rcs += repo.init()

        if 'backup' in args.action:
            rcs += repo.backup(config.get('backup'))
        if 'prune' in args.action:
            rcs += repo.forget(config.get('prune'))
            rcs += repo.prune()
        if 'check' in args.action:
            rcs += repo.check(config.get('check'))
        if 'stats' in args.action:
            rcs += repo.stats()

        logs['repositories'][repository] = repo.log

    if 'backup' in args.action and config.get('backup').get('post_hooks'):
        logs['restic_post_hooks'] = hooks.execute_hook(config, 'post_hooks')

    if log_metrics:
        logs['last_run'] = datetime.now().timestamp()
        logs['total_duration_seconds'] = time.time() - total_time
        write_lines(logs, config['name'], config.get('metrics'))

    if any(rcs):
        logger.error('There were problems in this run. Add `-l debug` to get a more comprehensive output')


def main():
    args = parse_arguments()
    signals.configure_signals()
    log.configure_logging(args.log_level)

    try:
        config_filenames = tuple(collect_config_filenames())

        if len(config_filenames) == 0:
            raise ValueError('Error: No configuration files found in {}'.format(get_default_config_paths()))

        configs = [parse_configuration(config_filename) for config_filename in config_filenames]

        if 'shell' in args.action:
            return restic_shell(configs)

        for config in configs:
            run_configuration(config, args)

    except (ValueError, OSError) as error:
        print(error)
        sys.exit(1)
