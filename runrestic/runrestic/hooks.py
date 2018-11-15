import logging
import subprocess

from runrestic.restic import ResticRepository

logger = logging.getLogger(__name__)


def execute_hook(config: dict, name: str, repo: ResticRepository):

    commands = config.get('backup').get(name, [])

    rcs = []

    for cmd in commands:
        logger.info(' - executing hook: {cmd}'.format(cmd=cmd))

        try:
            output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, universal_newlines=True, shell=True)
            process_rc = 0
        except subprocess.CalledProcessError as e:
            output = e.output
            process_rc = e.returncode

        logger.debug(output)

        logger.info('   ' + ("✓" if process_rc == 0 else "✕"))

        if config['exit_on_error'] and process_rc != 0:
            return process_rc

        rcs += [process_rc]

    if repo.log_metrics:
        repo.log['restic_{name}'.format(name=name)] = {}
        repo.log['restic_{name}'.format(name=name)]['rc'] = 1 if any(rcs) else 0

    return rcs
