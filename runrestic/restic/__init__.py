import json
import logging
import subprocess
import sys
import time

from runrestic.restic.output_parser import parse_prune, parse_backup, parse_forget
from runrestic.tools.converters import make_size

logger = logging.getLogger(__name__)


class ResticRepository:
    def __init__(self, repository, log_metrics, dry_run=False):
        self.repository = repository
        self.basecommand = ['restic', '-r', repository]
        self.log_metrics = log_metrics
        self.log = {}
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

    def backup(self, config):
        time_start = time.time()
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
            self.log['restic_backup']['duration_seconds'] = time.time() - time_start
            self.log['restic_backup']['rc'] = process_rc

        logger.info('   ' + ("✓" if process_rc == 0 else "✕"))
        return process_rc

    def forget(self, config):
        time_start = time.time()
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
            self.log['restic_forget']['duration_seconds'] = time.time() - time_start
            self.log['restic_forget']['rc'] = process_rc

        logger.info('   ' + ("✓" if process_rc == 0 else "✕"))
        return process_rc

    def prune(self):
        time_start = time.time()
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
            self.log['restic_prune']['duration_seconds'] = time.time() - time_start
            self.log['restic_prune']['rc'] = process_rc

        logger.info('   ' + ("✓" if process_rc == 0 else "✕"))
        return process_rc

    def check(self, consistency):
        time_start = time.time()
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
            self.log['restic_check']['duration_seconds'] = time.time() - time_start
            self.log['restic_check']['rc'] = process_rc

        logger.info('   ' + ("✓" if process_rc == 0 else "✕"))
        return process_rc

    def stats(self):
        time_start = time.time()
        logger.info(' - stats')

        cmd = self.basecommand + ['stats', '-q', '--json']

        try:
            output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, universal_newlines=True)
            process_rc = 1 if 'error:' in output else 0

            stats_json = json.loads(output)
            logger.debug(
                "Total File Count: {}\nTotal Size: {}".format(
                    stats_json['total_file_count'],
                    make_size(stats_json['total_size'])
                )
            )

            if self.log_metrics:
                self.log['restic_stats'] = stats_json
                self.log['restic_stats']['duration_seconds'] = time.time() - time_start
                self.log['restic_stats']['rc'] = process_rc

        except subprocess.CalledProcessError as e:
            if 'Is there a repository at the following location?' in e.output:
                logger.error("\nIt seems like the repo is not initialized. Run `runrestic init`.")
                sys.exit(1)
            output = e.output
            process_rc = e.returncode
            logger.error(output)

        except json.JSONDecodeError as e:
            raise e

        return process_rc
