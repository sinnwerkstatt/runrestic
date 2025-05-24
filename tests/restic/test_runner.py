from argparse import Namespace
from typing import Any
from unittest import TestCase
from unittest.mock import patch

from runrestic.restic import runner


class TestResticRunner(TestCase):
    @patch("runrestic.restic.runner.initialize_environment")
    def test_runner_class_init(self, mock_init_env):
        """
        Test the initialization of the Runner class.
        """
        config = {
            "dummy": "config",
            "repositories": ["dummy-repo"],
            "environment": {"dummy_env": "dummy_value"},
            "metrics": {"prometheus": {"password_replacement": "dummy_pw"}},
        }
        args = Namespace()
        args.dry_run = False
        restic_args = ["dummy-arg"]

        runner_instance = runner.ResticRunner(config, args, restic_args)
        self.assertEqual(runner_instance.args, args)
        self.assertEqual(runner_instance.restic_args, restic_args)
        self.assertTrue(runner_instance.log_metrics)
        self.assertEqual(runner_instance.pw_replacement, "dummy_pw")

    @patch.object(runner.ResticRunner, "init")
    @patch.object(runner.ResticRunner, "backup")
    @patch.object(runner.ResticRunner, "forget")
    @patch.object(runner.ResticRunner, "prune")
    @patch.object(runner.ResticRunner, "check")
    @patch.object(runner.ResticRunner, "stats")
    @patch.object(runner.ResticRunner, "unlock")
    @patch("runrestic.restic.runner.write_metrics")
    def test_run_dispatcher(
        self,
        mock_write_metrics,
        mock_unlock,
        mock_stats,
        mock_check,
        mock_prune,
        mock_forget,
        mock_backup,
        mock_init,
    ):
        """
        Dispatch scenarios for run():
          - all actions explicitly named
          - unknown action only
          - default actions with metrics enabled
          - default actions with metrics disabled
        """
        scenarios: list[dict[str, Any]] = [
            {
                "name": "all_actions",
                "config": {
                    "name": "test",
                    "repositories": ["repo"],
                    "environment": {},
                    "execution": {},
                    "metrics": {"prometheus": {}},
                },
                "actions": ["init", "backup", "prune", "check", "stats", "unlock"],
                "initial_errors": 2,
                "expected_calls": {
                    "init": 1,
                    "backup": 1,
                    "forget": 1,
                    "prune": 1,
                    "check": 1,
                    "stats": 1,
                    "unlock": 1,
                },
                "write_metrics": True,
                "expected_errors": 2,
            },
            {
                "name": "unknown_only",
                "config": {
                    "name": "test",
                    "repositories": ["repo"],
                    "environment": {},
                    "execution": {},
                    # no "metrics" key → log_metrics=False
                },
                "actions": ["unknown"],
                "initial_errors": 5,
                "expected_calls": {
                    "init": 0,
                    "backup": 0,
                    "forget": 0,
                    "prune": 0,
                    "check": 0,
                    "stats": 0,
                    "unlock": 0,
                },
                "write_metrics": False,
                "expected_errors": 5,
            },
            {
                "name": "default_with_stats",
                "config": {
                    "name": "test",
                    "repositories": ["repo"],
                    "environment": {},
                    "execution": {},
                    "metrics": {"prometheus": {}},
                },
                "actions": [],  # log_metrics=True → ["backup","prune","check","stats"]
                "initial_errors": 0,
                "expected_calls": {
                    "init": 0,
                    "backup": 1,
                    "forget": 1,
                    "prune": 1,
                    "check": 1,
                    "stats": 1,
                    "unlock": 0,
                },
                "write_metrics": True,
                "expected_errors": 0,
            },
            {
                "name": "default_no_stats",
                "config": {
                    "name": "test",
                    "repositories": ["repo"],
                    "environment": {},
                    "execution": {},
                    # no "metrics" → log_metrics=False → ["backup","prune","check"]
                },
                "actions": [],
                "initial_errors": 0,
                "expected_calls": {
                    "init": 0,
                    "backup": 1,
                    "forget": 1,
                    "prune": 1,
                    "check": 1,
                    "stats": 0,
                    "unlock": 0,
                },
                "write_metrics": False,
                "expected_errors": 0,
            },
        ]

        for sc in scenarios:
            with self.subTest(sc["name"]):
                args = Namespace(actions=sc["actions"])
                args.dry_run = False
                runner_instance = runner.ResticRunner(
                    sc["config"], args, restic_args=[]
                )
                runner_instance.metrics["errors"] = sc["initial_errors"]

                result = runner_instance.run()
                self.assertEqual(result, sc["expected_errors"])

                # verify each method was (or wasn't) called
                self.assertEqual(mock_init.call_count, sc["expected_calls"]["init"])
                self.assertEqual(mock_backup.call_count, sc["expected_calls"]["backup"])
                self.assertEqual(mock_forget.call_count, sc["expected_calls"]["forget"])
                self.assertEqual(mock_prune.call_count, sc["expected_calls"]["prune"])
                self.assertEqual(mock_check.call_count, sc["expected_calls"]["check"])
                self.assertEqual(mock_stats.call_count, sc["expected_calls"]["stats"])
                self.assertEqual(mock_unlock.call_count, sc["expected_calls"]["unlock"])

                # verify write_metrics
                if sc["write_metrics"]:
                    mock_write_metrics.assert_called_once_with(
                        runner_instance.metrics, sc["config"]
                    )
                else:
                    mock_write_metrics.assert_not_called()

                # reset mocks for next scenario
                for m in (
                    mock_init,
                    mock_backup,
                    mock_forget,
                    mock_prune,
                    mock_check,
                    mock_stats,
                    mock_unlock,
                    mock_write_metrics,
                ):
                    m.reset_mock()

    @patch("runrestic.restic.runner.MultiCommand")
    def test_init_runs_commands(self, mock_mc):
        """
        Test init() method runs MultiCommand with the correct parameters and processes output.
        """
        config = {
            "repositories": ["repo1", "repo2"],
            "environment": {},
            "execution": {},
        }
        args = Namespace(dry_run=False)
        restic_args: list[str] = []
        runner_instance = runner.ResticRunner(config, args, restic_args)

        # Simulate one success and one failure in init
        mock_mc.return_value.run.return_value = [
            {"output": [(0, "repo1 initialized")], "time": 0.1},
            {"output": [(1, "repo2 already initialized")], "time": 0.2},
        ]

        runner_instance.init()

        # Ensure MultiCommand was called with the correct command list
        expected_commands = [
            ["restic", "-r", "repo1", "init"],
            ["restic", "-r", "repo2", "init"],
        ]
        mock_mc.assert_called_once()
        actual_call_args = mock_mc.call_args[0][0]
        self.assertEqual(actual_call_args, expected_commands)

        # Validate run() was invoked
        mock_mc.return_value.run.assert_called_once()

    @patch("runrestic.restic.runner.MultiCommand")
    @patch("runrestic.restic.runner.parse_backup")
    @patch(
        "runrestic.restic.runner.redact_password", side_effect=lambda repo, repl: repo
    )
    def test_backup_metrics(self, mock_redact, mock_parse_backup, mock_mc):
        """
        Test backup() handles success and failure correctly and updates metrics and errors.
        """
        config = {
            "repositories": ["repo1", "repo2"],
            "environment": {},
            "execution": {},
            "backup": {
                "sources": ["/data"],
                "files_from": ["/data/files.txt"],
                "exclude_patterns": ["*.exclude"],
                "exclude_files": ["dummy_file"],
                "exclude_if_present": ["*.present"],
            },
            "metrics": {},
        }
        args = Namespace(dry_run=False)
        restic_args = ["--opt"]
        runner_instance = runner.ResticRunner(config, args, restic_args)
        process_success = {"output": [(0, "")], "time": 0.1}
        process_fail = {"output": [(1, "")], "time": 0.2}
        mock_mc.return_value.run.return_value = [process_success, process_fail]
        mock_parse_backup.return_value = {"parsed": True}

        runner_instance.backup()

        # validate MultiCommand instantiation
        expected_commands = [
            [
                "restic",
                "-r",
                "repo1",
                "backup",
                "--opt",
                "--files-from",
                "/data/files.txt",
                "--exclude",
                "*.exclude",
                "--exclude-file",
                "dummy_file",
                "--exclude-if-present",
                "*.present",
                "/data",
            ],
            [
                "restic",
                "-r",
                "repo2",
                "backup",
                "--opt",
                "--files-from",
                "/data/files.txt",
                "--exclude",
                "*.exclude",
                "--exclude-file",
                "dummy_file",
                "--exclude-if-present",
                "*.present",
                "/data",
            ],
        ]
        expected_abort = [
            "Fatal: unable to open config file",
            "Fatal: wrong password",
        ]
        mock_mc.assert_called_once_with(
            expected_commands, config["execution"], expected_abort
        )
        mock_mc.return_value.run.assert_called_once()

        metrics = runner_instance.metrics["backup"]
        self.assertEqual(metrics["repo1"], {"parsed": True})
        self.assertEqual(metrics["repo2"], {"rc": 1})
        self.assertEqual(runner_instance.metrics["errors"], 1)

    @patch("runrestic.restic.runner.MultiCommand")
    @patch("runrestic.restic.runner.parse_backup")
    @patch(
        "runrestic.restic.runner.redact_password", side_effect=lambda repo, repl: repo
    )
    def test_backup_with_pre_and_post_hooks(
        self, mock_redact, mock_parse_backup, mock_mc
    ):
        """
        Test backup() runs pre_hooks, the main backup, and post_hooks with correct arguments and metrics.
        """
        # Arrange
        config: dict[str, Any] = {
            "repositories": ["repo"],
            "environment": {},
            "execution": {"foo": "bar"},
            "backup": {
                "sources": ["data"],
                "pre_hooks": [["echo", "pre1"], ["echo", "pre2"]],
                "post_hooks": [["echo", "post1"], ["echo", "post2"]],
            },
            "metrics": {"prometheus": {"password_replacement": ""}},
        }
        args = Namespace(dry_run=False)
        restic_args = ["--opt"]
        runner_instance = runner.ResticRunner(config, args, restic_args)

        # Simulate runs
        pre_runs = [
            {"output": [(0, "")], "time": 0.5},
            {"output": [(0, "")], "time": 0.2},
        ]
        main_runs = [
            {"output": [(0, "")], "time": 1.0},
        ]
        post_runs = [
            {"output": [(0, "")], "time": 0.3},
            {"output": [(1, "")], "time": 0.1},
        ]
        # run() called three times: pre, main, post
        mock_mc.return_value.run.side_effect = [pre_runs, main_runs, post_runs]
        mock_parse_backup.return_value = {"parsed": True}

        # Act
        runner_instance.backup()

        # Assert MultiCommand instantiations
        hooks_cfg = config["execution"].copy()
        hooks_cfg.update({"parallel": False, "shell": True})

        calls = mock_mc.call_args_list
        # 1) pre_hooks
        self.assertEqual(calls[0][0][0], config["backup"]["pre_hooks"])
        self.assertEqual(calls[0][1], {"config": hooks_cfg})
        # 2) main backup
        expected_cmds = [
            [
                "restic",
                "-r",
                "repo",
                "backup",
                *restic_args,
                *config["backup"]["sources"],
            ]
        ]
        expected_abort = ["Fatal: unable to open config file", "Fatal: wrong password"]
        self.assertEqual(calls[1][0][0], expected_cmds)
        self.assertEqual(calls[1][0][1], config["execution"])
        self.assertEqual(calls[1][0][2], expected_abort)
        # 3) post_hooks
        self.assertEqual(calls[2][0][0], config["backup"]["post_hooks"])
        self.assertEqual(calls[2][1], {"config": hooks_cfg})

        # Assert metrics
        m = runner_instance.metrics["backup"]
        # pre_hooks
        self.assertAlmostEqual(m["_restic_pre_hooks"]["duration_seconds"], 0.7)
        self.assertEqual(m["_restic_pre_hooks"]["rc"], 0)
        # main backup
        self.assertEqual(m["repo"], {"parsed": True})
        # post_hooks
        self.assertAlmostEqual(m["_restic_post_hooks"]["duration_seconds"], 0.4)
        self.assertEqual(m["_restic_post_hooks"]["rc"], 1)
        # errors only increment on main backup failures (none here)
        self.assertEqual(runner_instance.metrics["errors"], 0)

    @patch("runrestic.restic.runner.MultiCommand")
    @patch("runrestic.restic.runner.logger.warning")
    @patch("runrestic.restic.runner.logger.info")
    def test_unlock_logs_success_and_failure(self, mock_info, mock_warning, mock_mc):
        """
        Test that unlock() logs info for successful unlocks and warning for failures.
        """
        config = {
            "repositories": ["repo1", "repo2"],
            "environment": {},
            "execution": {},
        }
        args = Namespace(dry_run=False)
        restic_args = ["--opt"]
        runner_instance = runner.ResticRunner(config, args, restic_args)

        # Simulate one successful unlock (0) and one failure (1)
        outputs = [
            {"output": [(0, "ok")]},
            {"output": [(1, "error")]},
        ]
        mock_mc.return_value.run.return_value = outputs

        runner_instance.unlock()

        # Verify MultiCommand was constructed correctly
        expected_cmds = [
            ["restic", "-r", "repo1", "unlock", *restic_args],
            ["restic", "-r", "repo2", "unlock", *restic_args],
        ]
        mock_mc.assert_called_once_with(
            expected_cmds,
            config=config["execution"],
            abort_reasons=[
                "Fatal: unable to open config file",
                "Fatal: wrong password",
            ],
        )
        mock_mc.return_value.run.assert_called_once()

        # Check logger calls
        mock_info.assert_called_once_with(outputs[0]["output"])
        mock_warning.assert_called_once_with(outputs[1]["output"])

    @patch("runrestic.restic.runner.MultiCommand")
    @patch("runrestic.restic.runner.parse_forget")
    @patch(
        "runrestic.restic.runner.redact_password", side_effect=lambda repo, repl: repo
    )
    def test_forget_metrics(self, mock_redact, mock_parse_forget, mock_mc):
        """
        Test forget() handles metrics parsing and errors correctly.
        """
        config = {
            "repositories": ["repo"],
            "environment": {},
            "execution": {},
            "prune": {"keep-last": 3},
        }
        args = Namespace(dry_run=True)
        restic_args: list[str] = []
        runner_instance = runner.ResticRunner(config, args, restic_args)
        process_info = {"output": [(0, "")], "time": 0.1}
        mock_mc.return_value.run.return_value = [process_info]
        mock_parse_forget.return_value = {"forgotten": True}

        runner_instance.forget()
        metrics = runner_instance.metrics["forget"]
        self.assertEqual(metrics["repo"], {"forgotten": True})
        self.assertEqual(runner_instance.metrics["errors"], 0)

    @patch("runrestic.restic.runner.MultiCommand")
    @patch("runrestic.restic.runner.parse_forget")
    @patch(
        "runrestic.restic.runner.redact_password", side_effect=lambda repo, repl: repo
    )
    def test_forget_failure_increments_errors(
        self,
        mock_redact,
        mock_parse_forget,
        mock_mc,
    ):
        """
        Test that forget() handles a non-zero return code by recording rc and incrementing errors,
        and does not call parse_forget on failure.
        """
        config = {
            "repositories": ["repo"],
            "environment": {},
            "execution": {},
            "prune": {"keep-last": 2},
        }
        args = Namespace(dry_run=True)  # dry_run should add "--dry-run"
        restic_args: list[str] = []
        runner_instance = runner.ResticRunner(config, args, restic_args)

        # Simulate failure return code
        failure_run = {"output": [(1, "error")], "time": 0.1}
        mock_mc.return_value.run.return_value = [failure_run]

        runner_instance.forget()

        # Should not parse on error
        mock_parse_forget.assert_not_called()

        # Metrics for repo should record rc only
        forget_metrics = runner_instance.metrics["forget"]
        self.assertEqual(forget_metrics["repo"], {"rc": 1})
        # Error counter should be incremented
        self.assertEqual(runner_instance.metrics["errors"], 1)

        # Ensure "--dry-run" was included in the command
        expected_cmds = [
            ["restic", "-r", "repo", "forget", "--dry-run", "--keep-last", "2"]
        ]
        mock_mc.assert_called_once_with(
            expected_cmds,
            config=config["execution"],
            abort_reasons=[
                "Fatal: unable to open config file",
                "Fatal: wrong password",
            ],
        )

    @patch("runrestic.restic.runner.MultiCommand")
    @patch("runrestic.restic.runner.parse_forget")
    @patch(
        "runrestic.restic.runner.redact_password", side_effect=lambda repo, repl: repo
    )
    def test_forget_with_group_by_and_success(
        self,
        mock_redact,
        mock_parse_forget,
        mock_mc,
    ):
        """
        Test that forget() includes '--group-by' when configured and calls parse_forget on success.
        """
        config = {
            "repositories": ["repo"],
            "environment": {},
            "execution": {},
            "prune": {"group-by": "tag"},
        }
        args = Namespace(dry_run=False)
        restic_args: list[str] = []
        runner_instance = runner.ResticRunner(config, args, restic_args)

        # Simulate successful run
        success_run = {"output": [(0, "ok")], "time": 0.2}
        mock_mc.return_value.run.return_value = [success_run]
        mock_parse_forget.return_value = {"forgotten": True}

        runner_instance.forget()

        # Should parse on success
        mock_parse_forget.assert_called_once_with(success_run)

        # Metrics should include parsed value
        forget_metrics = runner_instance.metrics["forget"]
        self.assertEqual(forget_metrics["repo"], {"forgotten": True})
        self.assertEqual(runner_instance.metrics["errors"], 0)

        # Ensure "--group-by tag" appears in the command
        expected_cmds = [["restic", "-r", "repo", "forget", "--group-by", "tag"]]
        mock_mc.assert_called_once_with(
            expected_cmds,
            config=config["execution"],
            abort_reasons=[
                "Fatal: unable to open config file",
                "Fatal: wrong password",
            ],
        )

    @patch("runrestic.restic.runner.MultiCommand")
    @patch("runrestic.restic.runner.parse_new_prune", side_effect=IndexError)
    @patch("runrestic.restic.runner.parse_prune")
    @patch(
        "runrestic.restic.runner.redact_password", side_effect=lambda repo, repl: repo
    )
    def test_prune_metrics_old_prune(
        self, mock_redact, mock_parse_prune, mock_new_prune, mock_mc
    ):
        """
        Test prune() falls back to parse_prune when parse_new_prune raises IndexError.
        """
        config = {
            "repositories": ["repo"],
            "environment": {},
            "execution": {},
        }
        args = Namespace(dry_run=False)
        restic_args: list[str] = []
        runner_instance = runner.ResticRunner(config, args, restic_args)
        process_info = {"output": [(0, "")], "time": 0.1}
        mock_mc.return_value.run.return_value = [process_info]
        mock_parse_prune.return_value = {"pruned": True}

        runner_instance.prune()
        metrics = runner_instance.metrics["prune"]
        self.assertEqual(metrics["repo"], {"pruned": True})

    @patch("runrestic.restic.runner.MultiCommand")
    @patch("runrestic.restic.runner.parse_new_prune")
    @patch(
        "runrestic.restic.runner.redact_password", side_effect=lambda repo, repl: repo
    )
    def test_prune_metrics_new_prune(self, mock_redact, mock_parse_new_prune, mock_mc):
        """
        Test prune() uses parse_new_prune when available.
        """
        config = {
            "repositories": ["repo"],
            "environment": {},
            "execution": {},
        }
        args = Namespace(dry_run=False)
        restic_args: list[str] = []
        runner_instance = runner.ResticRunner(config, args, restic_args)
        process_info = {"output": [(0, "")], "time": 0.1}
        mock_mc.return_value.run.return_value = [process_info]
        mock_parse_new_prune.return_value = {"new_pruned": True}

        runner_instance.prune()
        metrics = runner_instance.metrics["prune"]
        self.assertEqual(metrics["repo"], {"new_pruned": True})

    @patch("runrestic.restic.runner.MultiCommand")
    @patch("runrestic.restic.runner.parse_new_prune")
    @patch("runrestic.restic.runner.parse_prune")
    @patch(
        "runrestic.restic.runner.redact_password", side_effect=lambda repo, repl: repo
    )
    def test_prune_failure_increments_errors(
        self,
        mock_redact,
        mock_parse_prune,
        mock_parse_new_prune,
        mock_mc,
    ):
        """
        Test prune() handles a non-zero return code by recording rc and incrementing errors.
        """
        # Setup
        config = {
            "repositories": ["repo"],
            "environment": {},
            "execution": {},
        }
        args = Namespace(dry_run=False)
        restic_args: list[str] = []
        runner_instance = runner.ResticRunner(config, args, restic_args)

        # Simulate prune failure
        failure_run = {"output": [(1, "prune error")], "time": 0.1}
        mock_mc.return_value.run.return_value = [failure_run]

        # Execute
        runner_instance.prune()

        # Should not attempt to parse on error
        mock_parse_new_prune.assert_not_called()
        mock_parse_prune.assert_not_called()

        # Metrics should record the rc and errors should increment
        prune_metrics = runner_instance.metrics["prune"]
        self.assertEqual(prune_metrics["repo"], {"rc": 1})
        self.assertEqual(runner_instance.metrics["errors"], 1)

    @patch("runrestic.restic.runner.MultiCommand")
    @patch(
        "runrestic.restic.runner.redact_password", side_effect=lambda repo, repl: repo
    )
    @patch("runrestic.restic.runner.parse_stats")
    def test_stats_metrics(self, mock_parse_stats, mock_redact, mock_mc):
        """
        Test stats() calls parse_stats and updates metrics correctly.
        """
        config = {
            "repositories": ["repo"],
            "environment": {},
            "execution": {},
        }
        args = Namespace(dry_run=False)
        restic_args = ["--verbose"]
        runner_instance = runner.ResticRunner(config, args, restic_args)
        process_info = {"output": [(0, "")], "time": 0.1}
        mock_mc.return_value.run.return_value = [process_info]
        mock_parse_stats.return_value = {"stats": True}

        runner_instance.stats()
        metrics = runner_instance.metrics["stats"]
        self.assertEqual(metrics["repo"], {"stats": True})
        self.assertEqual(runner_instance.metrics["errors"], 0)

    @patch("runrestic.restic.runner.MultiCommand")
    @patch(
        "runrestic.restic.runner.redact_password", side_effect=lambda repo, repl: repo
    )
    @patch("runrestic.restic.runner.parse_stats")
    def test_stats_failure_increments_errors(
        self, mock_parse_stats, mock_redact, mock_mc
    ):
        """
        Test stats() handles return_code > 0 by recording rc and incrementing errors.
        """
        config = {
            "repositories": ["repo"],
            "environment": {},
            "execution": {},
        }
        args = Namespace(dry_run=False)
        restic_args = ["--verbose"]
        runner_instance = runner.ResticRunner(config, args, restic_args)

        # simulate failure
        process_info = {"output": [(1, "error occurred")], "time": 0.1}
        mock_mc.return_value.run.return_value = [process_info]

        runner_instance.stats()

        # parse_stats should NOT be called on failure
        mock_parse_stats.assert_not_called()

        metrics = runner_instance.metrics["stats"]
        # rc should be recorded
        self.assertEqual(metrics["repo"], {"rc": 1})
        # errors counter should have been incremented by 1
        self.assertEqual(runner_instance.metrics["errors"], 1)

    @patch("runrestic.restic.runner.MultiCommand")
    def test_check_metrics_with_and_without_options(self, mock_mc):
        """
        Test check() with and without check-options:
         - Verifies the --check-unused and --read-data flags
         - Asserts MultiCommand args and abort_reasons
         - Validates per-repo metrics and global error count
        """
        scenarios: list[dict[str, Any]] = [
            {
                "name": "base_check",
                "config": {
                    "repositories": ["repo"],
                    "environment": {},
                    "execution": {},
                },
                "expected_commands": [["restic", "-r", "repo", "check"]],
                "expected_stats": {
                    "check_unused": 0,
                    "read_data": 0,
                },
            },
            {
                "name": "check_unused",
                "config": {
                    "repositories": ["repo"],
                    "environment": {},
                    "execution": {},
                    "check": {
                        "checks": ["check-unused"],
                    },
                },
                "expected_commands": [
                    ["restic", "-r", "repo", "check", "--check-unused"]
                ],
                "expected_stats": {
                    "check_unused": 1,
                    "read_data": 0,
                },
            },
            {
                "name": "check_read_data",
                "config": {
                    "repositories": ["repo"],
                    "environment": {},
                    "execution": {},
                    "check": {
                        "checks": ["read-data"],
                    },
                },
                "expected_commands": [["restic", "-r", "repo", "check", "--read-data"]],
                "expected_stats": {
                    "check_unused": 0,
                    "read_data": 1,
                },
            },
        ]
        # simulate a failure output
        output_str = "error: load <snapshot/1234>\nPack ID does not match, corrupted"
        process_info = {"output": [(1, output_str)], "time": 0.5}
        mock_mc.return_value.run.return_value = [process_info]

        for sc in scenarios:
            with self.subTest(sc["name"]):
                # build config

                args = Namespace(dry_run=False)
                restic_args: list[str] = []
                runner_instance = runner.ResticRunner(sc["config"], args, restic_args)

                # clear any prior error count
                runner_instance.metrics["errors"] = 0

                # run
                runner_instance.check()

                # validate MultiCommand instantiation
                expected_commands = sc["expected_commands"]
                expected_abort = [
                    "Fatal: unable to open config file",
                    "Fatal: wrong password",
                ]
                mock_mc.assert_called_once_with(
                    expected_commands,
                    config=sc["config"]["execution"],
                    abort_reasons=expected_abort,
                )
                mock_mc.return_value.run.assert_called_once()

                # self.assertEqual(config, base_config)
                # combined per-repo metrics assertion
                expected_stats = {
                    "errors": 1,
                    "errors_snapshots": 1,
                    "errors_data": 1,
                    "check_unused": sc["expected_stats"]["check_unused"],
                    "read_data": sc["expected_stats"]["read_data"],
                    "duration_seconds": 0.5,
                    "rc": 1,
                }
                self.assertEqual(
                    runner_instance.metrics["check"]["repo"], expected_stats
                )

                # global errors counter
                self.assertEqual(runner_instance.metrics["errors"], 1)

                # reset between subtests
                mock_mc.reset_mock()

    @patch("runrestic.restic.runner.MultiCommand")
    def test_check_metrics_with_errors(self, mock_mc):
        """
        Test check() with and different error scenarios
        """
        config = {
            "repositories": ["repo"],
            "environment": {},
            "execution": {},
        }
        scenarios: list[dict[str, Any]] = [
            {
                "name": "return_code",
                "process_info": {"output": [(1, "error occurred")], "time": 0.1},
                "global_errors": 1,
                "check_errors": 0,
            },
            {
                "name": "load_error",
                "process_info": {
                    "output": [(0, "Test: error: load <snapshot/123>")],
                    "time": 0.1,
                },
                "global_errors": 0,
                "check_errors": 1,
            },
            {
                "name": "pack_id_mismatch",
                "process_info": {
                    "output": [(0, "Test: Pack ID does not match, WRONG")],
                    "time": 0.1,
                },
                "global_errors": 0,
                "check_errors": 1,
            },
        ]

        for sc in scenarios:
            with self.subTest(sc["name"]):
                # build config
                args = Namespace(dry_run=False)
                restic_args: list[str] = []
                runner_instance = runner.ResticRunner(config, args, restic_args)
                # clear any prior error count
                runner_instance.metrics["errors"] = 0
                # simulate failure
                mock_mc.return_value.run.return_value = [sc["process_info"]]
                # run
                runner_instance.check()
                mock_mc.return_value.run.assert_called_once()
                # global errors counter
                self.assertEqual(runner_instance.metrics["errors"], sc["global_errors"])
                # check errors counter
                self.assertEqual(
                    runner_instance.metrics["check"]["repo"]["errors"],
                    sc["check_errors"],
                )
                # reset between subtests
                mock_mc.reset_mock()
