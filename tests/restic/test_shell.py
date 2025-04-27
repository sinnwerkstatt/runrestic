import os
from unittest import TestCase
from unittest.mock import patch

from runrestic.restic import shell


class TestResticShell(TestCase):
    @patch("runrestic.restic.shell.logger")
    @patch("runrestic.restic.shell.sys.exit")
    def test_restic_shell_single_repo(self, mock_sys_exit, mock_logger):
        """
        Test the restic_shell function with a single repository configuration.
        """
        configs = [
            {
                "name": "TestConfig",
                "repositories": ["test_repo"],
                "environment": {"TEST_ENV": "test_value"},
            }
        ]

        with (
            patch("builtins.print") as mock_print,
            patch("runrestic.restic.shell.pty.spawn") as mock_spawn,
        ):
            shell.restic_shell(configs)

            mock_print.assert_any_call("Using: \033[1;92mTestConfig:test_repo\033[0m")
            mock_print.assert_any_call(
                "Spawning a new shell with the restic environment variables all set."
            )
            mock_spawn.assert_called_once_with(os.environ["SHELL"])
            mock_sys_exit.assert_called_once_with(0)

    @patch("runrestic.restic.shell.logger")
    @patch("builtins.input", return_value="1")
    @patch("runrestic.restic.shell.sys.exit")
    def test_restic_shell_multi_repo(self, mock_sys_exit, mock_input, mock_logger):
        """
        Test the restic_shell function with a multiple repositories configuration.
        """
        configs = [
            {
                "name": "TestConfig",
                "repositories": ["test_repo_1", "test_repo_2"],
                "environment": {"TEST_ENV": "test_value"},
            }
        ]

        with (
            patch("builtins.print") as mock_print,
            patch("runrestic.restic.shell.pty.spawn") as mock_spawn,
        ):
            shell.restic_shell(configs)

            mock_print.assert_any_call("Using: \033[1;92mTestConfig:test_repo_2\033[0m")
            mock_print.assert_any_call(
                "Spawning a new shell with the restic environment variables all set."
            )
            mock_spawn.assert_called_once_with(os.environ["SHELL"])
            mock_sys_exit.assert_called_once_with(0)

    @patch("runrestic.restic.shell.logger")
    @patch("builtins.input", return_value="X")
    @patch("runrestic.restic.shell.sys.exit")
    def test_restic_shell_multi_repo_invalid_selection(
        self, mock_sys_exit, mock_input, mock_logger
    ):
        """
        Test the restic_shell function with a multiple repositories configuration with invalid user selection.
        """
        configs = [
            {
                "name": "TestConfig",
                "repositories": ["test_repo_1", "test_repo_2"],
                "environment": {"TEST_ENV": "test_value"},
            }
        ]

        with self.assertRaises(ValueError) as context:
            shell.restic_shell(configs)

        self.assertEqual(
            str(context.exception),
            "invalid literal for int() with base 10: 'X'",
        )
