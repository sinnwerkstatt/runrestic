import logging


def configure_logging(level_string: str):
    level = logging.getLevelName(level_string.upper())
    log = logging.getLogger('runrestic')
    log.setLevel(level)
    handler = logging.StreamHandler()
    handler.setLevel(level)
    formatter = logging.Formatter('%(message)s')
    handler.setFormatter(formatter)
    log.addHandler(handler)
