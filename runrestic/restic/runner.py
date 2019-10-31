import argparse
import logging
import os

from runrestic.restic.output_parsing import (
    parse_backup,
    parse_forget,
    parse_prune,
    parse_stats,
    repo_init_check,
)
from runrestic.restic.spawn import run_multiple_commands
from runrestic.runrestic.tools import timethis

logger = logging.getLogger(__name__)


def initialize_environment(config: dict):
    for key, value in config.items():
        logger.debug(f"[Environment] {key}={value}")
        os.environ[key] = value

    if not (os.environ.get("HOME") or os.environ.get("XDG_CACHE_HOME")):
        os.environ["XDG_CACHE_HOME"] = "/var/cache"


class ResticRunner:
    times = {}

    def __init__(self, config: dict, args: argparse.Namespace):
        self.config = config
        self.args = args
        self.log_metrics = (
            config.get("metrics") and not args.dry_run and not args.actions == ["init"]
        )
        if self.log_metrics:
            self.metrics = {repo: {} for repo in config["repositories"]}

        initialize_environment(self.config.get("environment"))

    @timethis(times, name="total")
    def run(self):
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
            if action == "check":
                self.check()
            if action == "stats":
                self.stats()
            if action == "unlock":
                self.unlock()

        print(self.metrics)
        # if log_metrics:
        #     logs["last_run"] = datetime.now().timestamp()
        #     logs["total_duration_seconds"] = time.time() - total_time
        #     write_lines(logs, config["name"], config.get("metrics"))

    @timethis(times)
    def init(self):
        commands = [
            (repo, ["restic", "-r", repo, "init"])
            for repo in self.config["repositories"]
        ]
        outputs = run_multiple_commands(commands, config=self.config["execution"])

        for repo, returncode, output in outputs:
            if returncode > 0:
                logger.warning(output)
            else:
                logger.info(output)

    @timethis(times)
    def backup(self):
        backup_cfg = self.config["backup"]

        if backup_cfg.get("pre_hooks"):
            commands = self.config["backup"].get("pre_hooks", [])
            outputs = run_multiple_commands(
                commands, config={"parallel": False, "shell": True}
            )

        commands = []
        for repo in self.config["repositories"]:
            cmd = ["restic", "-r", repo, "backup"] + backup_cfg.get("sources")
            for exclude_pattern in backup_cfg.get("exclude_patterns", []):
                cmd += ["--exclude", exclude_pattern]
            for exclude_file in backup_cfg.get("exclude_files", []):
                cmd += ["--exclude-file", exclude_file]
            commands += [(repo, cmd)]
        outputs = run_multiple_commands(commands, config=self.config["execution"])
        for repo, returncode, output in outputs:
            if returncode > 0:
                repo_init_check(output)
                continue
            if self.log_metrics:
                self.metrics[repo]["restic_backup"] = parse_backup(output)
            # if self.log_metrics:
            #     self.log["restic_backup"]["duration_seconds"] = time.time() - time_start
            #     self.log["restic_backup"]["rc"] = process_rc

        if backup_cfg.get("post_hooks"):
            commands = self.config["backup"].get("post_hooks", [])
            outputs = run_multiple_commands(
                commands, config={"parallel": False, "shell": True}
            )

    @timethis(times)
    def unlock(self):
        commands = [
            (repo, ["restic", "-r", repo, "unlock"])
            for repo in self.config["repositories"]
        ]

        run_multiple_commands(commands, config=self.config["execution"])

    @timethis(times)
    def forget(self):
        commands = []
        for repo in self.config["repositories"]:
            cmd = ["restic", "-r", repo, "forget"]
            if self.args.dry_run:
                cmd += ["--dry-run"]

            for key, value in self.config["prune"].items():
                if key.startswith("keep-"):
                    cmd += ["--{key}".format(key=key), str(value)]
                if key == "group-by":
                    cmd += ["--group-by", value]

            commands += [(repo, cmd)]

        outputs = run_multiple_commands(commands, config=self.config["execution"])
        for repo, returncode, output in outputs:
            if returncode > 0:
                repo_init_check(output)
                continue
            metrics = parse_forget(output)
            print(metrics)

        # if self.log_metrics:
        #     self.log["restic_forget"] = parse_forget(output)
        #     self.log["restic_forget"]["duration_seconds"] = time.time() - time_start
        #     self.log["restic_forget"]["rc"] = process_rc

    @timethis(times)
    def prune(self):
        commands = [
            (repo, ["restic", "-r", repo, "prune"])
            for repo in self.config["repositories"]
        ]

        outputs = run_multiple_commands(commands, config=self.config["execution"])
        for repo, returncode, output in outputs:
            if returncode > 0:
                repo_init_check(output)
                continue
            metrics = parse_prune(output)
            print(metrics)
        # if self.log_metrics:
        #     self.log["restic_prune"] = parse_prune(output)
        #     self.log["restic_prune"]["duration_seconds"] = time.time() - time_start
        #     self.log["restic_prune"]["rc"] = process_rc

    # @timethis(times)
    # def check(self, consistency):
    #     cmd = self.basecommand + ["check"]
    #
    #     metrics = {
    #         "errors": 0,
    #         "errors_data": 0,
    #         "errors_snapshots": 0,
    #         "read_data": 0,
    #         "check_unused": 0,
    #     }
    #
    #     if consistency and "checks" in consistency:
    #         if "check-unused" in consistency.get("checks"):
    #             cmd += ["--check-unused"]
    #             metrics["check_unused"] = 1
    #
    #         if "read-data" in consistency.get("checks"):
    #             cmd += ["--read-data"]
    #             metrics["read_data"] = 1
    #
    #     logger.debug(" ".join(cmd))
    #     try:
    #         output = subprocess.check_output(
    #             cmd, stderr=subprocess.STDOUT, universal_newlines=True
    #         )
    #         process_rc = 1 if "error:" in output else 0
    #         logger.debug(output)
    #     except subprocess.CalledProcessError as e:
    #         self._repo_init_check(e)
    #         output = e.output
    #         process_rc = e.returncode
    #         logger.error(output)
    #
    #         metrics["errors"] = 1
    #         if "error: load <snapshot/" in output:
    #             metrics["errors_snapshots"] = 1
    #         if "Pack ID does not match," in output:
    #             metrics["errors_data"] = 1
    #
    #     if self.log_metrics:
    #         self.log["restic_check"] = metrics
    #         self.log["restic_check"]["duration_seconds"] = time.time() - time_start
    #         self.log["restic_check"]["rc"] = process_rc
    #

    @timethis(times)
    def stats(self):
        commands = [
            (repo, ["restic", "-r", repo, "stats", "-q", "--json"])
            for repo in self.config["repositories"]
        ]

        outputs = run_multiple_commands(commands, config=self.config["execution"])

        for repo, returncode, output in outputs:
            if returncode > 0:
                repo_init_check(output)
                continue
            if self.log_metrics:
                self.metrics[repo]["restic_stats"] = parse_stats(output)
        #     if self.log_metrics:
        #         self.log["restic_stats"]["duration_seconds"] = time.time() - time_start
        #         self.log["restic_stats"]["rc"] = process_rc
        #
