import io
import logging
import os
import time
from time import sleep
from typing import Any
from unittest.mock import MagicMock, call, patch

import pytest

from runrestic.restic.tools import (
    MultiCommand,
    initialize_environment,
    redact_password,
    retry_process,
)


def fake_retry_process(
    cmd: str | list[str],
    config: dict[str, Any],
    abort_reasons: list[str] | None = None,
) -> dict[str, Any]:
    """Fake retry_process function to simulate command execution."""
    # Simulate different outputs per command
    if isinstance(cmd, list):
        cmd = cmd[0]
    try:
        count = int(cmd[-1])
    except ValueError:
        count = 1
    retry_count = config.get("retry_count", 0)
    sleep(count / 10)  # Simulate some processing time
    return {
        "current_try": count,
        "tries_total": 3,
        "output": [(1, f"fail{i}") for i in range(1, count)]
        + ([(0, "pass")] if retry_count + 1 >= count else []),
        "time": count / 10,
    }


def fake_process(returncode: int, stdout_text: str) -> MagicMock:
    """Helper to create a fake Popen-like process object."""
    proc = MagicMock()
    proc.__enter__.return_value = proc
    proc.__exit__.return_value = None
    proc.stdout = io.StringIO(stdout_text)
    proc.returncode = returncode
    return proc


@pytest.mark.parametrize(
    "popen_results, retry_count, expected_output, expected_current, expected_total",
    [
        (  # Test immediate success with no no reties allowed
            [fake_process(0, "pass"), fake_process(0, "extra")],
            0,
            [(0, "pass")],
            1,
            1,
        ),
        (  # Test immediate success with 1 retry allowed
            [fake_process(0, "pass"), fake_process(0, "extra")],
            1,
            [(0, "pass")],
            1,
            2,
        ),
        (  # Test 1 failure with 1 retry allowed, finally passing
            [
                fake_process(1, "fail1"),
                fake_process(0, "pass"),
                fake_process(0, "extra"),
            ],
            1,
            [(1, "fail1"), (0, "pass")],
            2,
            2,
        ),
        (  # Test 2 failures with 1 retry allowed, finally failing
            [
                fake_process(1, "fail1"),
                fake_process(1, "fail2"),
                fake_process(0, "extra"),
            ],
            1,
            [(1, "fail1"), (1, "fail2")],
            2,
            2,
        ),
        (  # Test 4 failures and 5th success with 4 retries allowed, finally passing
            [
                fake_process(1, "fail1"),
                fake_process(1, "fail2"),
                fake_process(1, "fail3"),
                fake_process(1, "fail4"),
                fake_process(0, "pass"),
                fake_process(0, "extra"),
            ],
            4,
            [
                (1, "fail1"),
                (1, "fail2"),
                (1, "fail3"),
                (1, "fail4"),
                (0, "pass"),
            ],
            5,
            5,
        ),
        (  # Test 3 failures with 2 retries allowed, finally failing
            [
                fake_process(1, "fail1"),
                fake_process(1, "fail2"),
                fake_process(1, "fail3"),
                fake_process(0, "extra"),
            ],
            2,
            [(1, "fail1"), (1, "fail2"), (1, "fail3")],
            3,
            3,
        ),
    ],
)
@patch("runrestic.restic.tools.Popen")
def test_retry_process(
    mock_popen: MagicMock,
    popen_results,
    retry_count,
    expected_output,
    expected_current,
    expected_total,
):
    # Arrange
    mock_popen.side_effect = popen_results

    # Act
    result = retry_process(["dummy_command"], {"retry_count": retry_count})

    # Assert
    assert "time" in result, "Result should include execution time"
    assert result["output"] == expected_output
    assert result["current_try"] == expected_current
    assert result["tries_total"] == expected_total


@pytest.mark.parametrize(
    "backoff, expected_sleep_args",
    [
        ("0:01", [1, 1, 1]),
        ("0:01 linear", [1, 2, 3]),
        ("0:01 exponential", [1, 2, 4]),
    ],
)
@patch("runrestic.restic.tools.time.sleep")
@patch("runrestic.restic.tools.Popen")
def test_retry_process_backoff(
    mock_popen: MagicMock,
    mock_sleep: MagicMock,
    backoff,
    expected_sleep_args,
):
    # Arrange
    mock_popen.side_effect = [fake_process(1, f"call {i + 1}/3") for i in range(3)]

    # Act
    p = retry_process(
        ["dummy_command"],
        {"retry_count": 2, "retry_backoff": backoff},
    )

    # Assert sleeps
    expected_calls = [call(arg) for arg in expected_sleep_args]
    mock_sleep.assert_has_calls(expected_calls)

    # Remove timing and output details for comparison
    p.pop("time")
    p.pop("output")
    assert p == {"current_try": 3, "tries_total": 3}


@patch("runrestic.restic.tools.Popen")
def test_retry_process_with_abort_reason(mock_popen: MagicMock):
    # Call the retry_process function with mocked Popen
    mock_popen.return_value = fake_process(99, "Abort reason: 1/10")
    p = retry_process(
        ["dummy_command"],
        {"retry_count": 99},
        abort_reasons=[": 1/10"],
    )
    # Validate the results
    assert p["current_try"] == 1
    assert p["tries_total"] == 100


@patch("runrestic.restic.tools.retry_process", new=fake_retry_process)
def test_run_multiple_commands_parallel() -> None:
    cmds = ["dummy_cmd3", "dummy_cmd2", "dummy_cmd1"]
    config = {"retry_count": 2, "parallel": True, "retry_backoff": "0:01"}
    start_time = time.time()
    aa = MultiCommand(cmds, config).run()
    assert 0.5 > time.time() - start_time > 0.3
    expected_return = [[1, 1, 0], [1, 0], [0]]

    for exp, cmd_ret in zip(expected_return, aa, strict=False):
        assert [x[0] for x in cmd_ret["output"]] == exp


@patch("runrestic.restic.tools.retry_process", new=fake_retry_process)
def test_run_multiple_commands_serial() -> None:
    cmds = ["dummy_cmd3", "dummy_cmd3", "dummy_cmd4"]
    config = {"retry_count": 2, "parallel": False, "retry_backoff": "0:01"}
    start_time = time.time()
    aa = MultiCommand(cmds, config).run()
    assert 1.1 > float(time.time() - start_time) > 0.5
    expected_return = [[1, 1, 0], [1, 1, 0], [1, 1, 1]]

    for exp, cmd_ret in zip(expected_return, aa, strict=False):
        assert [x[0] for x in cmd_ret["output"]] == exp


def test_initialize_environment_pw_redact(caplog):
    env = {"RESTIC_PASSWORD": "my$ecr3T"}
    caplog.set_level(logging.DEBUG)
    initialize_environment(env)
    assert "RESTIC_PASSWORD=**********" in caplog.text
    assert "my$ecr3T" not in caplog.text


def test_initialize_environment_no_home(monkeypatch):
    env = {"TEST123": "xyz"}
    monkeypatch.setenv("HOME", "")
    initialize_environment(env)
    assert os.environ.get("TEST123") == "xyz"
    assert os.environ.get("XDG_CACHE_HOME") == "/var/cache"


def test_initialize_environment_user(monkeypatch):
    env = {"TEST456": "abc"}
    monkeypatch.setenv("HOME", "/home/user")
    monkeypatch.setenv("XDG_CACHE_HOME", "/home/user/.cache")
    initialize_environment(env)
    assert os.environ.get("TEST456") == "abc"
    assert os.environ.get("XDG_CACHE_HOME") == "/home/user/.cache"


def test_initialize_environment_root(monkeypatch):
    env = {"TEST789": "qpr"}
    monkeypatch.setenv("HOME", "/root")
    monkeypatch.setenv("XDG_CACHE_HOME", "/root/.cache")
    monkeypatch.setattr(os, "geteuid", lambda: 0)  # fake root
    initialize_environment(env)
    assert os.environ.get("TEST789") == "qpr"
    assert os.environ.get("XDG_CACHE_HOME") == "/var/cache"


def test_redact_password():
    password = "my$ecr3T"  # noqa: S105
    repo_strings = [
        "ftp://user:{}@server.com",
        "rest:http://user:{}@test1.something.org",
        "rest:https://user:{}@a-123.what.us",
        "s3:http://user:{}@lost.data.net",
        "s3:https://user:{}@island.in.the.sun.co.uk",
    ]
    pw_replacement = "******"
    for repo_str in repo_strings:
        assert redact_password(
            repo_str.format(password), pw_replacement
        ) == repo_str.format(pw_replacement)
