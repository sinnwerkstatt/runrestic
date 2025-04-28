import logging
import os
import signal
from unittest import TestCase
from unittest.mock import MagicMock, patch

from runrestic.runrestic import runrestic


class TestRunresticRunrestic(TestCase):
    def test_configure_logging_levels(self):
        """
        Parameterized test to ensure configure_logging correctly sets logger level,
        adds a StreamHandler at that level, and uses the "%(message)s" formatter.
        """
        levels_to_test = ["error", "info", "debug"]
        logger_name = "runrestic"

        for level_str in levels_to_test:
            with self.subTest(level=level_str):
                logger = logging.getLogger(logger_name)

                # Backup and clear handlers
                original_handlers = logger.handlers[:]
                logger.handlers.clear()

                try:
                    runrestic.configure_logging(level_str)

                    expected_level = logging.getLevelName(level_str.upper())

                    # Check logger level
                    self.assertEqual(logger.level, expected_level)

                    # Check StreamHandler with correct level
                    stream_handlers = [
                        h for h in logger.handlers if isinstance(h, logging.StreamHandler) and h.level == expected_level
                    ]
                    self.assertTrue(stream_handlers, f"No StreamHandler with level {level_str.upper()} found")

                    # Check formatter format
                    for handler in stream_handlers:
                        formatter = handler.formatter
                        self.assertIsNotNone(formatter, "Handler has no formatter")
                        self.assertEqual(
                            formatter._fmt,  # type: ignore[union-attr]
                            "%(message)s",
                            "Formatter format is not '%(message)s'",
                        )
                finally:
                    # Restore original handlers
                    logger.handlers = original_handlers

    def test_handlers_registered_and_kill_group(self):
        """
        Test that configure_signals registers handlers for the expected signals
        and that invoking each handler inside the patch context calls os.killpg
        with the current process group, without killing the test process.
        """
        registered = {}

        def fake_signal(sig, handler):
            registered[sig] = handler
            return None

        fake_pgid = 12345

        with (
            patch("signal.signal", new=fake_signal),
            patch("os.getpgrp", return_value=fake_pgid),
            patch("os.killpg") as mock_killpg,
        ):
            runrestic.configure_signals()

            # Ensure handlers are registered for the expected signals
            expected_signals = {
                signal.SIGINT,
                signal.SIGHUP,
                signal.SIGTERM,
                signal.SIGUSR1,
                signal.SIGUSR2,
            }
            self.assertEqual(
                set(registered.keys()),
                expected_signals,
                f"Expected registrations for {expected_signals}, got {set(registered.keys())}",
            )

            # Invoke each handler inside the patch context to ensure killpg is mocked
            for sig in expected_signals:
                handler = registered[sig]
                self.assertTrue(callable(handler), f"Handler for {sig} is not callable")
                handler(sig, None)
                mock_killpg.assert_called_with(fake_pgid, sig)
                mock_killpg.reset_mock()

    @patch("runrestic.runrestic.runrestic.restic_check", return_value=False)
    def test_no_resto_binary(self, mock_check):
        # If restic_check() is False, runrestic returns early
        self.assertIsNone(runrestic.runrestic())  # type: ignore[func-returns-value]
        mock_check.assert_called_once()

    @patch("runrestic.runrestic.runrestic.parse_configuration", side_effect=KeyError("Error"))
    @patch("runrestic.runrestic.runrestic.configure_logging")
    @patch("runrestic.runrestic.runrestic.restic_check", return_value=True)
    @patch("runrestic.runrestic.runrestic.cli_arguments")
    def test_config_file_flag(self, mock_cli, mock_check, mock_log, mock_parse):
        args = MagicMock()
        args.log_level = "info"
        args.config_file = "/tmp/config"  # noqa: S108
        args.actions = []
        args.show_progress = None
        extras: list[str] = []
        mock_cli.return_value = (args, extras)

        # with patch("runrestic.runrestic.runrestic.parse_configuration", return_value={"cfg": 1}):
        with self.assertRaises(KeyError):
            runrestic.runrestic()
        mock_parse.assert_called_once_with("/tmp/config")  # noqa: S108
        mock_log.assert_called_with("info")

    @patch("runrestic.runrestic.runrestic.restic_check", return_value=True)
    @patch("runrestic.runrestic.runrestic.cli_arguments")
    @patch("runrestic.runrestic.runrestic.configuration_file_paths", return_value=[])
    @patch("runrestic.runrestic.runrestic.possible_config_paths", return_value=["/etc/restic", "~/.restic"])
    def test_no_config_paths_raises(self, mock_possible, mock_confpaths, mock_cli, mock_check):
        args = MagicMock(log_level="debug", config_file=None, actions=[], show_progress=None)
        extras: list[str] = []
        mock_cli.return_value = (args, extras)
        with self.assertRaises(FileNotFoundError):
            runrestic.runrestic()

    @patch("runrestic.runrestic.runrestic.restic_check", return_value=True)
    @patch("runrestic.runrestic.runrestic.cli_arguments")
    @patch("runrestic.runrestic.runrestic.configuration_file_paths", return_value=["cfg1"])
    @patch("runrestic.runrestic.runrestic.parse_configuration", return_value={})
    def test_show_progress_sets_env(self, mock_parse, mock_conf_paths, mock_cli, mock_check):
        args = MagicMock(log_level="info", config_file=None, actions=[], show_progress="0.5")
        extras: list[str] = []
        mock_cli.return_value = (args, extras)

        runrestic.runrestic()
        self.assertIn("RESTIC_PROGRESS_FPS", os.environ)
        self.assertEqual(os.environ["RESTIC_PROGRESS_FPS"], str(1 / float("0.5")))

    @patch("runrestic.runrestic.runrestic.restic_check", return_value=True)
    @patch("runrestic.runrestic.runrestic.cli_arguments")
    @patch("runrestic.runrestic.runrestic.configuration_file_paths", return_value=["cfg1"])
    @patch(
        "runrestic.runrestic.runrestic.parse_configuration",
        return_value={"repositories": ["dummy"], "name": "dummy", "environment": {}},
    )
    @patch("runrestic.runrestic.runrestic.restic_shell")
    def test_shell_action_invokes_shell(self, mock_shell, mock_parse, mock_confpaths, mock_cli, mock_check):
        with patch("runrestic.runrestic.runrestic.logging.getLogger") as _mock_get_logger:
            _mock_logger = MagicMock()
            args = MagicMock(log_level="info", config_file=None, actions=["shell"], show_progress=None)
            extras: list[str] = []
            mock_cli.return_value = (args, extras)

            result = runrestic.runrestic()  # type: ignore[func-returns-value]
            mock_shell.assert_called_once_with([{"repositories": ["dummy"], "name": "dummy", "environment": {}}])
            self.assertIsNone(result)

    @patch("runrestic.runrestic.runrestic.restic_check", return_value=True)
    @patch("runrestic.runrestic.runrestic.cli_arguments")
    @patch("runrestic.runrestic.runrestic.configuration_file_paths", return_value=["cfg1", "cfg2"])
    @patch("runrestic.runrestic.runrestic.parse_configuration", return_value={"a": 1})
    @patch("runrestic.runrestic.runrestic.ResticRunner")
    def test_runner_exit_codes(self, mock_runner_cls, mock_parse, mock_confpaths, mock_cli, mock_check):
        args = MagicMock(log_level="info", config_file=None, actions=[], show_progress=None)
        extras: list[str] = []
        mock_cli.return_value = (args, extras)

        # runner one returns 0, runner two returns 2 -> sum=2 >0 -> sys.exit(1)
        runner1 = MagicMock(run=MagicMock(return_value=0))
        runner2 = MagicMock(run=MagicMock(return_value=2))
        mock_runner_cls.side_effect = [runner1, runner2]

        with self.assertRaises(SystemExit) as cm:
            runrestic.runrestic()
        self.assertEqual(cm.exception.code, 1)
