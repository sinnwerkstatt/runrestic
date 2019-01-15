from runrestic.metrics.prometheus import prometheus_write_file
from .prometheus import prometheus_generate_lines


def write_lines(metrics: dict, config_name: str, configuration: dict):
    if 'prometheus' in configuration.keys():
        lines = prometheus_generate_lines(metrics, config_name)
        return prometheus_write_file(lines, configuration.get('prometheus')['path'])
