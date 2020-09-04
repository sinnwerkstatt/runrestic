from argparse import Namespace
import json
import logging
import time
from datetime import datetime
from typing import Any, Dict, List

from runrestic.metrics import write_metrics
from runrestic.restic.output_parsing import (
    parse_backup,
    parse_forget,
    parse_prune,
    parse_stats,
)
from runrestic.restic.tools import MultiCommand, initialize_environment

logger = logging.getLogger(__name__)


class ResticRunner:
    def __init__(
        self, config: Dict[str, Any], args: Namespace, restic_args: List[str]
    ) -> None:
        self.config = config
        self.args = args
        self.restic_args = restic_args

        self.repos = self.config["repositories"]

        self.metrics: Dict[str, Any] = {"errors": 0}
        self.log_metrics = config.get("metrics") and not args.dry_run

        initialize_environment(self.config["environment"])

    def run(self) -> None:
        start_time = time.time()
        actions = self.args.actions

        if not actions and self.log_metrics:
            actions = ["backup", "prune", "check", "stats"]
        elif not actions:
            actions = ["backup", "prune", "check"]

        for action in actions:
            if action == "init":
                self.init()
            elif action == "backup":
                self.backup()
            elif action == "prune":
                self.forget()
                self.prune()
            elif action == "check":
                self.check()
            elif action == "stats":
                self.stats()
            elif action == "unlock":
                self.unlock()

        self.metrics["last_run"] = datetime.now().timestamp()
        self.metrics["total_duration_seconds"] = time.time() - start_time

        logger.debug(json.dumps(self.metrics, indent=2))

        if self.log_metrics:
            write_metrics(self.metrics, self.config)

    def init(self) -> None:
        commands = [
            ["restic", "-r", repo, "init"] + self.restic_args for repo in self.repos
        ]

        direct_abort_reasons = ["config file already exists"]
        cmd_runs = MultiCommand(
            commands, self.config["execution"], direct_abort_reasons
        ).run()

        for process_infos in cmd_runs:
            if process_infos["output"][-1][0] > 0:
                logger.warning(process_infos["output"])
            else:
                logger.info(process_infos["output"])

    def backup(self) -> None:
        metrics = self.metrics["backup"] = {}
        cfg = self.config["backup"]

        hooks_cfg = self.config["execution"].copy()
        hooks_cfg.update({"parallel": False, "shell": True})

        # backup pre_hooks
        if cfg.get("pre_hooks"):
            cmd_runs = MultiCommand(cfg["pre_hooks"], config=hooks_cfg).run()
            metrics["_restic_pre_hooks"] = {
                "duration_seconds": sum([v["time"] for v in cmd_runs]),
                "rc": sum(x["output"][-1][0] for x in cmd_runs),
            }

        # actual backup
        extra_args: List[str] = []
        for files_from in cfg.get("files_from", []):
            extra_args += ["--files-from", files_from]
        for exclude_pattern in cfg.get("exclude_patterns", []):
            extra_args += ["--exclude", exclude_pattern]
        for exclude_file in cfg.get("exclude_files", []):
            extra_args += ["--exclude-file", exclude_file]

        commands = [
            ["restic", "-r", repo, "backup"]
            + self.restic_args
            + extra_args
            + cfg.get("sources", [])
            for repo in self.repos
        ]
        direct_abort_reasons = ["Fatal: unable to open config file"]
        cmd_runs = MultiCommand(
            commands, self.config["execution"], direct_abort_reasons
        ).run()

        for repo, process_infos in zip(self.repos, cmd_runs):
            rc = process_infos["output"][-1][0]
            if rc > 0:
                logger.warning(process_infos)
                metrics[repo] = {"rc": rc}
                self.metrics["errors"] += 1
            else:
                metrics[repo] = parse_backup(process_infos)

        # backup post_hooks
        if cfg.get("post_hooks"):
            cmd_runs = MultiCommand(cfg["post_hooks"], config=hooks_cfg).run()
            metrics["_restic_post_hooks"] = {
                "duration_seconds": sum(v["time"] for v in cmd_runs),
                "rc": sum(x["output"][-1][0] for x in cmd_runs),
            }

    def unlock(self) -> None:
        commands = [
            ["restic", "-r", repo, "unlock"] + self.restic_args for repo in self.repos
        ]

        cmd_runs = MultiCommand(commands, config=self.config["execution"]).run()
        for process_infos in cmd_runs:
            if process_infos["output"][-1][0] > 0:
                logger.warning(process_infos["output"])
            else:
                logger.info(process_infos["output"])

    def forget(self) -> None:
        metrics = self.metrics["forget"] = {}

        extra_args: List[str] = []
        if self.args.dry_run:
            extra_args += ["--dry-run"]
        for key, value in self.config["prune"].items():
            if key.startswith("keep-"):
                extra_args += [f"--{key}", str(value)]
            if key == "group-by":
                extra_args += ["--group-by", value]

        commands = [
            ["restic", "-r", repo, "forget"] + self.restic_args + extra_args
            for repo in self.repos
        ]
        cmd_runs = MultiCommand(commands, config=self.config["execution"]).run()

        for repo, process_infos in zip(self.repos, cmd_runs):
            rc = process_infos["output"][-1][0]
            if rc > 0:
                logger.warning(process_infos["output"])
                metrics[repo] = {"rc": rc}
                self.metrics["errors"] += 1
            else:
                metrics[repo] = parse_forget(process_infos)

    def prune(self) -> None:
        metrics = self.metrics["prune"] = {}

        commands = [
            ["restic", "-r", repo, "prune"] + self.restic_args for repo in self.repos
        ]
        cmd_runs = MultiCommand(commands, config=self.config["execution"]).run()

        for repo, process_infos in zip(self.repos, cmd_runs):
            rc = process_infos["output"][-1][0]
            if rc > 0:
                logger.warning(process_infos["output"])
                metrics[repo] = {"rc": rc}
                self.metrics["errors"] += 1
            else:
                metrics[repo] = parse_prune(process_infos)

    def check(self) -> None:
        self.metrics["check"] = {}

        extra_args: List[str] = []
        cfg = self.config.get("check")
        if cfg and "checks" in cfg:
            checks = cfg["checks"]
            if "check-unused" in checks:
                extra_args += ["--check-unused"]
            if "read-data" in checks:
                extra_args += ["--read-data"]

        commands = [
            ["restic", "-r", repo, "check"] + self.restic_args + extra_args
            for repo in self.repos
        ]
        cmd_runs = MultiCommand(commands, config=self.config["execution"]).run()

        for repo, process_infos in zip(self.repos, cmd_runs):
            metrics = {
                "errors": 0,
                "errors_data": 0,
                "errors_snapshots": 0,
                "read_data": 1 if "read_data" in extra_args else 0,
                "check_unused": 1 if "--check-unused" in extra_args else 0,
            }
            rc, output = process_infos["output"][-1]
            if rc > 0:
                logger.warning(process_infos["output"])
            if "error: load <snapshot/" in output:
                metrics["errors_snapshots"] = 1
                metrics["errors"] = 1
            if "Pack ID does not match," in output:
                metrics["errors_data"] = 1
                metrics["errors"] = 1
            metrics["duration_seconds"] = process_infos["time"]
            metrics["rc"] = rc
            self.metrics["check"][repo] = metrics

    def stats(self) -> None:
        metrics = self.metrics["stats"] = {}

        commands = [
            ["restic", "-r", repo, "stats", "-q", "--json"] + self.restic_args
            for repo in self.repos
        ]
        cmd_runs = MultiCommand(commands, config=self.config["execution"]).run()

        for repo, process_infos in zip(self.repos, cmd_runs):
            rc = process_infos["output"][-1][0]
            if rc > 0:
                logger.warning(process_infos["output"])
                metrics[repo] = {"rc": rc}
                self.metrics["errors"] += 1
            else:
                metrics[repo] = parse_stats(process_infos)
