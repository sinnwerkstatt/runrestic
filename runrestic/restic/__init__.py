import json
import logging
import subprocess

logger = logging.getLogger(__name__)


class ResticRepository:
    def __init__(self, repository, config, check_initialization=True):
        self.basecommand = ['restic', '-r', repository]
        self.config = config
        self.initialized = self.check_initialization() if check_initialization else None
        self.dry_run = config['args'].dry_run

    def init(self):
        logger.info('Restic::Init')
        if self.initialized is True:
            logger.warning('Repo already initialized')
            return

        cmd = self.basecommand + ['init']

        logger.debug(" ".join(cmd))
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, universal_newlines=True)
        logger.debug(output)

    def snapshots(self):
        cmd = self.basecommand + ['snapshots', '--json']

        try:
            output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, universal_newlines=True)
        except subprocess.CalledProcessError as e:
            if 'config: no such file or directory' in e.output:
                return False
            raise e
        try:
            snapshots_json = json.loads(output)
            # logger.debug(snapshots_json)
        except json.JSONDecodeError as e:
            raise e
        return snapshots_json

    def check_initialization(self):
        snapshots = self.snapshots()
        return bool(snapshots)

    def backup(self):
        if not self.initialized:
            logger.error("Can't backup to uninitialized repo")
            return

        cmd = self.basecommand + ['backup']

        location = self.config.get('location')
        for exclude_pattern in location.get('exclude_patterns', []):
            cmd += ['--exclude', exclude_pattern]
        for exclude_file in location.get('exclude_files', []):
            cmd += ['--exclude-file', exclude_file]

        if not location.get('source_directories'):
            raise Exception("You need to specify source_directories.")
        cmd += location.get('source_directories')

        logger.debug(" ".join(cmd))
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, universal_newlines=True)
        logger.debug(output)

    def forget(self, prune=True):
        if not self.initialized:
            logger.error("Repo is not initialized")
            return
        cmd = self.basecommand + ['forget']
        if prune:
            cmd += ['--prune']

        if self.dry_run:
            cmd += ['--dry-run']

        retention = self.config.get('retention')
        for key, value in retention.items():
            if key.startswith('keep-'):
                cmd += [f'--{key}', str(value)]

        logger.debug(" ".join(cmd))
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, universal_newlines=True)
        logger.debug(output)
