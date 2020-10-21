from typing import Any, Dict

from . import prometheus


def write_metrics(metrics: Dict[str, Any], config: Dict[str, Any]) -> None:
    configuration = config["metrics"]
    if "prometheus" in configuration.keys():
        lines = prometheus.generate_lines(metrics, config["name"])

        with open(configuration["prometheus"]["path"], "w") as file:
            file.writelines("".join(lines))
