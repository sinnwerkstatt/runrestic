from runrestic.metrics.prometheus import prometheus_write_file
from .prometheus import prometheus_generate_lines


def generate_lines(metrics: dict, repository, config_name: str, configuration: dict):
    if 'prometheus' in configuration.keys():
        return prometheus_generate_lines(metrics, repository, config_name)


def write_lines(lines: str, configuration: dict):
    if 'prometheus' in configuration.keys():
        return prometheus_write_file(lines, configuration.get('prometheus')['path'])
