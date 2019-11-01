from runrestic.metrics.prometheus import prometheus_write_file

from .prometheus import prometheus_generate_lines


def write_metrics(metrics: dict, config: dict):
    configuration = config["metrics"]
    if "prometheus" in configuration.keys():
        lines = prometheus_generate_lines(metrics, config["name"])
        return prometheus_write_file(lines, configuration["prometheus"]["path"])
