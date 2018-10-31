import os


def initialize_environment(environment_config):
    if not (os.environ.get('HOME') or os.environ.get('XDG_CACHE_HOME')):
        os.environ['XDG_CACHE_HOME'] = '/var/cache'

    if not (environment_config.get('RESTIC_PASSWORD') or environment_config.get('RESTIC_PASSWORD_FILE')):
        raise Exception("You need to specify either a password or a password_file")

    for key, value in environment_config.items():
        os.environ[key] = value
