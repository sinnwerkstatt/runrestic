import argparse
import json
import logging
import time
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict

from runrestic.restic.output_parsing import (
    parse_backup,
    parse_forget,
    parse_prune,
    parse_stats,
    repo_init_check,
)
from runrestic.restic.tools import initialize_environment, run_multiple_commands

logger = logging.getLogger(__name__)


def recursive_dict():
    return defaultdict(recursive_dict)


class ResticRunner:
    def __init__(self, config: dict, args: argparse.Namespace):
        self.config = config
        self.args = args

        self.repos = self.config["repositories"]

        self.metrics: Dict[str, Any] = {}
        self.log_metrics = config.get("metrics") and not args.dry_run

        initialize_environment(self.config["environment"])

    def run(self):
        start_time = time.time()
        actions = self.args.actions

        if not actions and self.log_metrics:
            actions = ["backup", "prune", "check", "stats"]
        elif not actions:
            actions = ["backup", "prune", "check"]

        for action in actions:
            if action == "init":
                self.init()
            if action == "backup":
                self.backup()
            if action == "prune":
                self.forget()
                self.prune()
            # TODO!
            # if action == "check":
            #     self.check()
            if action == "stats":
                self.stats()
            if action == "unlock":
                self.unlock()

        self.metrics["last_run"] = datetime.now().timestamp()
        self.metrics["total_duration_seconds"] = time.time() - start_time

        logger.debug(json.dumps(self.metrics, indent=2))

        if self.log_metrics:
            # write_metrics(self.metrics, self.config)
            pass

    def init(self):
        commands = [(repo, ["restic", "-r", repo, "init"]) for repo in self.repos]

        cmd_runs = run_multiple_commands(commands, config=self.config["execution"])

        for repo, p_infos in cmd_runs.items():
            if p_infos["output"][-1][0] > 0:
                logger.warning(p_infos["output"])
            else:
                logger.info(p_infos["output"])

    def backup(self):
        metrics = self.metrics["backup"] = {}
        backup_cfg = self.config["backup"]

        # backup pre_hooks
        if backup_cfg.get("pre_hooks"):
            cmd_runs = run_multiple_commands(
                backup_cfg["pre_hooks"], config={"parallel": False, "shell": True}
            )
            metrics["_restic_pre_hooks"] = {
                "duration_seconds": sum(
                    [v["timer"].duration() for v in cmd_runs.values()]
                )
            }

        # actual backup
        extra_args = []
        for exclude_pattern in backup_cfg.get("exclude_patterns", []):
            extra_args += ["--exclude", exclude_pattern]
        for exclude_file in backup_cfg.get("exclude_files", []):
            extra_args += ["--exclude-file", exclude_file]

        commands = [
            (
                repo,
                (
                    ["restic", "-r", repo, "backup"]
                    + extra_args
                    + backup_cfg.get("sources")
                ),
            )
            for repo in self.repos
        ]

        cmd_runs = run_multiple_commands(commands, config=self.config["execution"])

        for repo, p_infos in cmd_runs.items():
            if p_infos["returncode"] > 0:
                repo_init_check(p_infos["output"])
                continue
            metrics[repo] = parse_backup(p_infos)

        # backup post_hooks
        if backup_cfg.get("post_hooks"):
            cmd_runs = run_multiple_commands(
                backup_cfg["post_hooks"], config={"parallel": False, "shell": True}
            )
            metrics["_restic_post_hooks"] = {
                "duration_seconds": sum(
                    [v["timer"].duration() for v in cmd_runs.values()]
                )
            }

    def unlock(self):
        commands = [(repo, ["restic", "-r", repo, "unlock"]) for repo in self.repos]

        run_multiple_commands(commands, config=self.config["execution"])

    def forget(self):
        metrics = self.metrics["forget"] = {}

        extra_args = []
        if self.args.dry_run:
            extra_args += ["--dry-run"]
        for key, value in self.config["prune"].items():
            if key.startswith("keep-"):
                extra_args += ["--{key}".format(key=key), str(value)]
            if key == "group-by":
                extra_args += ["--group-by", value]

        commands = [
            (repo, ["restic", "-r", repo, "forget"] + extra_args) for repo in self.repos
        ]

        cmd_runs = run_multiple_commands(commands, config=self.config["execution"])

        for repo, p_infos in cmd_runs.items():
            if p_infos["returncode"] > 0:
                repo_init_check(p_infos["output"])
                continue
            metrics[repo] = parse_forget(p_infos)

    def prune(self):
        metrics = self.metrics["prune"] = {}

        commands = [(repo, ["restic", "-r", repo, "prune"]) for repo in self.repos]

        cmd_runs = run_multiple_commands(commands, config=self.config["execution"])

        for repo, p_infos in cmd_runs.items():
            if p_infos["returncode"] > 0:
                repo_init_check(p_infos["output"])
                continue
            metrics[repo] = parse_prune(p_infos)

    def check(self):
        check_cfg = self.config.get("check")
        metrics = {
            "errors": 0,
            "errors_data": 0,
            "errors_snapshots": 0,
            "read_data": 0,
            "check_unused": 0,
        }

        extra_args = []
        if check_cfg and "checks" in check_cfg:
            checks = check_cfg["checks"]
            if "check-unused" in checks:
                extra_args += ["--check-unused"]
                metrics["check_unused"] = 1
            if "read-data" in checks:
                extra_args += ["--read-data"]
                metrics["read_data"] = 1

        commands = [
            (repo, ["restic", "-r", repo, "check"] + extra_args) for repo in self.repos
        ]

        cmd_runs = run_multiple_commands(commands, config=self.config["execution"])

        for repo, p_infos in cmd_runs.items():
            if p_infos["returncode"] > 0:
                repo_init_check(p_infos["output"])
                continue
            metrics[repo] = parse_check(p_infos)

        #     metrics["errors"] = 1
        #     if "error: load <snapshot/" in output:
        #         metrics["errors_snapshots"] = 1
        #     if "Pack ID does not match," in output:
        #         metrics["errors_data"] = 1
        #
        # if self.log_metrics:
        #     self.log["restic_check"] = metrics
        #     self.log["restic_check"]["duration_seconds"] = time.time() - time_start
        #     self.log["restic_check"]["rc"] = process_rc

    def stats(self):
        metrics = self.metrics["stats"] = {}

        commands = [
            (repo, ["restic", "-r", repo, "stats", "-q", "--json"])
            for repo in self.repos
        ]

        cmd_runs = run_multiple_commands(commands, config=self.config["execution"])

        for repo, p_infos in cmd_runs.items():
            if p_infos["returncode"] > 0:
                repo_init_check(p_infos["output"])
                continue
            metrics[repo] = parse_stats(p_infos)
