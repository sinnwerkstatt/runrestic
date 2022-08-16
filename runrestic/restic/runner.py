import json
import logging
import re
import time
from argparse import Namespace
from datetime import datetime
from typing import Any, Dict, List

from runrestic.metrics import write_metrics
from runrestic.restic.output_parsing import (
    parse_backup,
    parse_forget,
    parse_new_prune,
    parse_prune,
    parse_stats,
)
from runrestic.restic.tools import MultiCommand, initialize_environment, redact_password

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
        self.pw_replacement = (
            config.get("metrics", {})
            .get("prometheus", {})
            .get("password_replacement", "")
        )

        initialize_environment(self.config["environment"])

    def run(self) -> Any:
        start_time = time.time()
        actions = self.args.actions

        if not actions and self.log_metrics:
            actions = ["backup", "prune", "check", "stats"]
        elif not actions:
            actions = ["backup", "prune", "check"]

        logger.info("Starting '%s': %s", self.config["name"], actions)
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

        return self.metrics["errors"]

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
        for exclude_if_present in cfg.get("exclude_if_present", []):
            extra_args += ["--exclude-if-present", exclude_if_present]

        commands = [
            ["restic", "-r", repo, "backup"]
            + self.restic_args
            + extra_args
            + cfg.get("sources", [])
            for repo in self.repos
        ]
        direct_abort_reasons = [
            "Fatal: unable to open config file",
            "Fatal: wrong password",
        ]
        cmd_runs = MultiCommand(
            commands, self.config["execution"], direct_abort_reasons
        ).run()

        for repo, process_infos in zip(self.repos, cmd_runs):
            return_code = process_infos["output"][-1][0]
            if return_code > 0:
                logger.warning(process_infos)
                metrics[redact_password(repo, self.pw_replacement)] = {
                    "rc": return_code
                }
                self.metrics["errors"] += 1
            else:
                metrics[redact_password(repo, self.pw_replacement)] = parse_backup(
                    process_infos
                )

        # backup post_hooks
        if cfg.get("post_hooks"):
            cmd_runs = MultiCommand(cfg["post_hooks"], config=hooks_cfg).run()
            metrics["_restic_post_hooks"] = {
                "duration_seconds": sum(v["time"] for v in cmd_runs),
                "rc": sum(x["output"][-1][0] for x in cmd_runs),
            }

    def unlock(self) -> None:
        direct_abort_reasons = [
            "Fatal: unable to open config file",
            "Fatal: wrong password",
        ]
        commands = [
            ["restic", "-r", repo, "unlock"] + self.restic_args for repo in self.repos
        ]

        cmd_runs = MultiCommand(
            commands,
            config=self.config["execution"],
            abort_reasons=direct_abort_reasons,
        ).run()
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

        direct_abort_reasons = [
            "Fatal: unable to open config file",
            "Fatal: wrong password",
        ]
        commands = [
            ["restic", "-r", repo, "forget"] + self.restic_args + extra_args
            for repo in self.repos
        ]
        cmd_runs = MultiCommand(
            commands,
            config=self.config["execution"],
            abort_reasons=direct_abort_reasons,
        ).run()

        for repo, process_infos in zip(self.repos, cmd_runs):
            return_code = process_infos["output"][-1][0]
            if return_code > 0:
                logger.warning(process_infos["output"])
                metrics[redact_password(repo, self.pw_replacement)] = {
                    "rc": return_code
                }
                self.metrics["errors"] += 1
            else:
                metrics[redact_password(repo, self.pw_replacement)] = parse_forget(
                    process_infos
                )

    def prune(self) -> None:
        metrics = self.metrics["prune"] = {}

        direct_abort_reasons = [
            "Fatal: unable to open config file",
            "Fatal: wrong password",
        ]
        commands = [
            ["restic", "-r", repo, "prune"] + self.restic_args for repo in self.repos
        ]
        cmd_runs = MultiCommand(
            commands,
            config=self.config["execution"],
            abort_reasons=direct_abort_reasons,
        ).run()

        for repo, process_infos in zip(self.repos, cmd_runs):
            return_code = process_infos["output"][-1][0]
            if return_code > 0:
                logger.warning(process_infos["output"])
                metrics[redact_password(repo, self.pw_replacement)] = {
                    "rc": return_code
                }
                self.metrics["errors"] += 1
            else:
                try:
                    metrics[
                        redact_password(repo, self.pw_replacement)
                    ] = parse_new_prune(process_infos)
                except IndexError:
                    # assume we're dealing with restic <0.12.0
                    metrics[redact_password(repo, self.pw_replacement)] = parse_prune(
                        process_infos
                    )

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

        direct_abort_reasons = [
            "Fatal: unable to open config file",
            "Fatal: wrong password",
        ]
        commands = [
            ["restic", "-r", repo, "check"] + self.restic_args + extra_args
            for repo in self.repos
        ]
        cmd_runs = MultiCommand(
            commands,
            config=self.config["execution"],
            abort_reasons=direct_abort_reasons,
        ).run()

        for repo, process_infos in zip(self.repos, cmd_runs):
            metrics = {
                "errors": 0,
                "errors_data": 0,
                "errors_snapshots": 0,
                "read_data": 1 if "read_data" in extra_args else 0,
                "check_unused": 1 if "--check-unused" in extra_args else 0,
            }
            return_code, output = process_infos["output"][-1]
            if return_code > 0:
                logger.warning(process_infos["output"])
                self.metrics["errors"] += 1
            if "error: load <snapshot/" in output:
                metrics["errors_snapshots"] = 1
                metrics["errors"] = 1
            if "Pack ID does not match," in output:
                metrics["errors_data"] = 1
                metrics["errors"] = 1
            metrics["duration_seconds"] = process_infos["time"]
            metrics["rc"] = return_code
            self.metrics["check"][redact_password(repo, self.pw_replacement)] = metrics

    def stats(self) -> None:
        metrics = self.metrics["stats"] = {}

        direct_abort_reasons = [
            "Fatal: unable to open config file",
            "Fatal: wrong password",
        ]
        # quiet and verbose arguments are mutually exclusive
        verbose = re.compile(r"^--verbose")
        quiet = [] if list(filter(verbose.match, self.restic_args)) else ["-q"]
        commands = [
            ["restic", "-r", repo, "stats", "--json"] + quiet + self.restic_args
            for repo in self.repos
        ]
        cmd_runs = MultiCommand(
            commands,
            config=self.config["execution"],
            abort_reasons=direct_abort_reasons,
        ).run()

        for repo, process_infos in zip(self.repos, cmd_runs):
            return_code = process_infos["output"][-1][0]
            if return_code > 0:
                logger.warning(process_infos["output"])
                metrics[redact_password(repo, self.pw_replacement)] = {
                    "rc": return_code
                }
                self.metrics["errors"] += 1
            else:
                metrics[redact_password(repo, self.pw_replacement)] = parse_stats(
                    process_infos
                )
