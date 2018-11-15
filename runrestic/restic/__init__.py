import json
import logging
import subprocess
import sys
from datetime import datetime
from typing import Dict, Any

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
            }  # type: Dict[str, Any]
        self.dry_run = dry_run

    def init(self):
        logger.info(' - init')

        cmd = self.basecommand + ['init']

        logger.debug(" ".join(cmd))
        try:
            output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, universal_newlines=True)
            process_rc = 0
            logger.debug(output)
        except subprocess.CalledProcessError as e:
            output = e.output
            process_rc = e.returncode
            logger.error(output)

        logger.info('   ' + ("✓" if process_rc == 0 else "✕"))
        return process_rc

    # this is currently not needed.
    # def snapshots(self):
    #     cmd = self.basecommand + ['snapshots', '--json']
    #
    #     logger.debug(" ".join(cmd))
    #     try:
    #         output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, universal_newlines=True)
    #         logger.debug(output)
    #     except subprocess.CalledProcessError as e:
    #         if 'config: no such file or directory' in e.output:
    #             return False
    #         logger.error(e.output)
    #         raise e
    #
    #     try:
    #         snapshots_json = json.loads(output)
    #         # logger.debug(snapshots_json)
    #     except json.JSONDecodeError as e:
    #         raise e
    #     return snapshots_json
    #
    # def check_initialization(self):
    #     snapshots = self.snapshots()
    #     if snapshots == False:
    #         return False
    #     return True

    def backup(self, config):
        logger.info(' - backup')

        cmd = self.basecommand + ['backup']

        if not config.get('sources'):
            raise Exception("You need to specify sources in [backup].")
        cmd += config.get('sources')

        for exclude_pattern in config.get('exclude_patterns', []):
            cmd += ['--exclude', exclude_pattern]
        for exclude_file in config.get('exclude_files', []):
            cmd += ['--exclude-file', exclude_file]

        logger.debug(" ".join(cmd))
        try:
            output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, universal_newlines=True)
            process_rc = 1 if 'error:' in output else 0
            logger.debug(output)
        except subprocess.CalledProcessError as e:
            if 'Is there a repository at the following location?' in e.output:
                logger.error("\nIt seems like the repo is not initialized. Run `runrestic init`.")
                sys.exit(1)
            output = e.output
            process_rc = e.returncode
            logger.error(output)

        if self.log_metrics:
            self.log['restic_backup'] = parse_backup(output)
            self.log['restic_backup']['rc'] = process_rc

        logger.info('   ' + ("✓" if process_rc == 0 else "✕"))
        return process_rc

    def forget(self, config):
        logger.info(' - forget')

        cmd = self.basecommand + ['forget']

        if self.dry_run:
            cmd += ['--dry-run']

        for key, value in config.items():
            if key.startswith('keep-'):
                cmd += ['--{key}'.format(key=key), str(value)]

        logger.debug(" ".join(cmd))
        try:
            output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, universal_newlines=True)
            process_rc = 1 if 'error:' in output else 0
            logger.debug(output)
        except subprocess.CalledProcessError as e:
            if 'Is there a repository at the following location?' in e.output:
                logger.error("\nIt seems like the repo is not initialized. Run `runrestic init`.")
                sys.exit(1)
            output = e.output
            process_rc = e.returncode
            logger.error(output)

        if self.log_metrics:
            self.log['restic_forget'] = parse_forget(output)
            self.log['restic_forget']['rc'] = process_rc

        logger.info('   ' + ("✓" if process_rc == 0 else "✕"))
        return process_rc

    def prune(self):
        logger.info(" - prune")

        cmd = self.basecommand + ['prune']

        logger.debug(" ".join(cmd))
        try:
            output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, universal_newlines=True)
            process_rc = 1 if 'error:' in output else 0
            logger.debug(output)
        except subprocess.CalledProcessError as e:
            if 'Is there a repository at the following location?' in e.output:
                logger.error("\nIt seems like the repo is not initialized. Run `runrestic init`.")
                sys.exit(1)
            output = e.output
            process_rc = e.returncode
            logger.error(output)

        if self.log_metrics:
            self.log['restic_prune'] = parse_prune(output)
            self.log['restic_prune']['rc'] = process_rc

        logger.info('   ' + ("✓" if process_rc == 0 else "✕"))
        return process_rc

    def check(self, consistency):
        logger.info(' - check')

        cmd = self.basecommand + ['check']

        metrics = {
            'errors': 0, 'errors_data': 0, 'errors_snapshots': 0,
            'read_data': 0, 'check_unused': 0,
        }

        if consistency and 'checks' in consistency:
            if 'check-unused' in consistency.get('checks'):
                cmd += ['--check-unused']
                metrics['check_unused'] = 1

            if 'read-data' in consistency.get('checks'):
                cmd += ['--read-data']
                metrics['read_data'] = 1

        logger.debug(" ".join(cmd))
        try:
            output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, universal_newlines=True)
            process_rc = 1 if 'error:' in output else 0
            logger.debug(output)
        except subprocess.CalledProcessError as e:
            if 'Is there a repository at the following location?' in e.output:
                logger.error("\nIt seems like the repo is not initialized. Run `runrestic init`.")
                sys.exit(1)
            output = e.output
            process_rc = e.returncode
            logger.error(output)

            metrics['errors'] = 1
            if "error: load <snapshot/" in output:
                metrics['errors_snapshots'] = 1
            if "Pack ID does not match," in output:
                metrics['errors_data'] = 1

        if self.log_metrics:
            self.log['restic_check'] = metrics
            self.log['restic_check']['rc'] = process_rc

        logger.info('   ' + ("✓" if process_rc == 0 else "✕"))
        return process_rc
