import json
import logging
import subprocess
from datetime import datetime

from runrestic.restic.output_parser import parse_prune, parse_backup, parse_forget

logger = logging.getLogger(__name__)


class ResticRepository:
    def __init__(self, repository, log_metrics, dry_run=False):
        self.repository = repository
        self.basecommand = ['restic', '-r', repository]
        self.log_metrics = log_metrics
        if self.log_metrics:
            self.log = {
                'last_run': datetime.now().timestamp(),
            }
        self.dry_run = dry_run
        self.initialized = self.check_initialization()

    def init(self):
        logger.info(f'Restic::Init::{self.repository}')

        if self.initialized is True:
            logger.warning('Repo already initialized')
            return

        cmd = self.basecommand + ['init']
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, universal_newlines=True)
        logger.debug(" ".join(cmd))
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
        if snapshots == False:
            return False
        return True

    def backup(self, location):
        logger.info(f'Restic::Backup::{self.repository}')
        if not self.initialized:
            logger.error("Repo is not initialized")
            return

        cmd = self.basecommand + ['backup']

        if not location.get('source_directories'):
            raise Exception("You need to specify source_directories.")
        cmd += location.get('source_directories')

        for exclude_pattern in location.get('exclude_patterns', []):
            cmd += ['--exclude', exclude_pattern]
        for exclude_file in location.get('exclude_files', []):
            cmd += ['--exclude-file', exclude_file]

        try:
            output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, universal_newlines=True)
            process_rc = 0
        except subprocess.CalledProcessError as e:
            output = e.output
            process_rc = e.returncode

        logger.debug(" ".join(cmd))
        logger.debug(output)

        if self.log_metrics:
            self.log['restic_backup'] = parse_backup(output)
            self.log['restic_backup']['rc'] = process_rc

    def forget(self, retention):
        logger.info(f'Restic::Forget::{self.repository}')
        if not self.initialized:
            logger.error("Repo is not initialized")
            return

        cmd = self.basecommand + ['forget']

        if self.dry_run:
            cmd += ['--dry-run']

        for key, value in retention.items():
            if key.startswith('keep-'):
                cmd += [f'--{key}', str(value)]

        try:
            output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, universal_newlines=True)
            process_rc = 0
        except subprocess.CalledProcessError as e:
            output = e.output
            process_rc = e.returncode

        logger.debug(" ".join(cmd))
        logger.debug(output)

        if self.log_metrics:
            self.log['restic_forget'] = parse_forget(output)
            self.log['restic_forget']['rc'] = process_rc

    def prune(self):
        logger.info(f'Restic::Prune::{self.repository}')
        if not self.initialized:
            logger.error("Repo is not initialized")
            return

        cmd = self.basecommand + ['prune']

        try:
            output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, universal_newlines=True)
            process_rc = 0
        except subprocess.CalledProcessError as e:
            output = e.output
            process_rc = e.returncode

        logger.debug(" ".join(cmd))
        logger.debug(output)

        if self.log_metrics:
            self.log['restic_prune'] = parse_prune(output)
            self.log['restic_prune']['rc'] = process_rc

    def check(self, consistency):
        logger.info(f'Restic::Check::{self.repository}')
        if not self.initialized:
            logger.error("Repo is not initialized")
            return

        cmd = self.basecommand + ['check']

        metrics = {
            'errors': False, 'errors_data': False, 'errors_snapshots': False,
            'read_data': False, 'check_unused': False,
        }

        if 'check-unused' in consistency.get('checks'):
            cmd += ['--check-unused']
            metrics['check_unused'] = True

        if 'read-data' in consistency.get('checks'):
            cmd += ['--read-data']
            metrics['read_data'] = True

        try:
            output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, universal_newlines=True)
            process_rc = 0
        except subprocess.CalledProcessError as e:
            output = e.output
            process_rc = e.returncode

            metrics['errors'] = True
            if "error: load <snapshot/" in output:
                metrics['errors_snapshots'] = True
            if "Pack ID does not match," in output:
                metrics['errors_data'] = True

        logger.debug(" ".join(cmd))
        logger.debug(output)

        if self.log_metrics:
            self.log['restic_check'] = metrics
            self.log['restic_check']['rc'] = process_rc
