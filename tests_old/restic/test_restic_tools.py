import logging
import os
import time

from runrestic.restic.tools import (
    MultiCommand,
    initialize_environment,
    redact_password,
    retry_process,
)


def test_retry_process(tmpdir):
    p = retry_process(
        ["python", "tests/retry_testing_tool.py", "1", "a", tmpdir], {"retry_count": 0}
    )
    p.pop("time")
    assert p.pop("output") == [(0, "")]
    assert p == {"current_try": 1, "tries_total": 1}

    p = retry_process(
        ["python", "tests/retry_testing_tool.py", "1", "b", tmpdir], {"retry_count": 1}
    )
    p.pop("time")
    assert p.pop("output") == [(0, "")]
    assert p == {"current_try": 1, "tries_total": 2}

    p = retry_process(
        ["python", "tests/retry_testing_tool.py", "2", "c", tmpdir], {"retry_count": 1}
    )
    p.pop("time")
    p.pop("output")
    assert p == {"current_try": 2, "tries_total": 2}

    p = retry_process(
        ["python", "tests/retry_testing_tool.py", "3", "d", tmpdir], {"retry_count": 1}
    )
    p.pop("time")
    p.pop("output")
    assert p == {"current_try": 2, "tries_total": 2}

    p = retry_process(
        ["python", "tests/retry_testing_tool.py", "5", "f", tmpdir], {"retry_count": 4}
    )
    p.pop("time")
    p.pop("output")
    assert p == {"current_try": 5, "tries_total": 5}

    p = retry_process(
        ["python", "tests/retry_testing_tool.py", "4", "h", tmpdir], {"retry_count": 2}
    )
    p.pop("time")
    p.pop("output")
    assert p == {"current_try": 3, "tries_total": 3}


def test_retry_process_with_backoff(tmpdir):
    p = retry_process(
        ["python", "tests/retry_testing_tool.py", "3", "i", tmpdir],
        {"retry_count": 2, "retry_backoff": "0:01"},
    )
    assert 3 > p.pop("time") > 2
    p.pop("output")
    assert p == {"current_try": 3, "tries_total": 3}

    p = retry_process(
        ["python", "tests/retry_testing_tool.py", "3", "j", tmpdir],
        {"retry_count": 2, "retry_backoff": "0:01 linear"},
    )
    assert 4 > p.pop("time") > 3
    p.pop("output")
    assert p == {"current_try": 3, "tries_total": 3}

    p = retry_process(
        ["python", "tests/retry_testing_tool.py", "3", "k", tmpdir],
        {"retry_count": 2, "retry_backoff": "0:01 exponential"},
    )
    assert 4 > p.pop("time") > 3
    p.pop("output")
    assert p == {"current_try": 3, "tries_total": 3}


def test_retry_process_with_abort_reason(tmpdir):
    p = retry_process(
        ["python", "tests/retry_testing_tool.py", "10", "aaa", tmpdir],
        {"retry_count": 99},
        abort_reasons=[": 1/10"],
    )
    p.pop("time")
    assert p.pop("output")[-1][0] == 1
    assert p == {"current_try": 1, "tries_total": 100}


def test_run_multiple_commands_parallel(tmpdir):
    cmds = [
        ["python", "tests/retry_testing_tool.py", "3", "l", tmpdir],
        ["python", "tests/retry_testing_tool.py", "2", "m", tmpdir],
        ["python", "tests/retry_testing_tool.py", "1", "n", tmpdir],
    ]
    config = {"retry_count": 2, "parallel": True, "retry_backoff": "0:01"}
    start_time = time.time()
    aa = MultiCommand(cmds, config).run()
    assert 3 > time.time() - start_time > 2
    expected_return = [[1, 1, 0], [1, 0], [0]]

    for exp, cmd_ret in zip(expected_return, aa):
        assert [x[0] for x in cmd_ret["output"]] == exp


def test_run_multiple_commands_serial(tmpdir):
    cmds = [
        ["python", "tests/retry_testing_tool.py", "3", "o", tmpdir],
        ["python", "tests/retry_testing_tool.py", "3", "p", tmpdir],
        ["python", "tests/retry_testing_tool.py", "4", "q", tmpdir],
    ]
    config = {"retry_count": 2, "parallel": False, "retry_backoff": "0:01"}
    start_time = time.time()
    aa = MultiCommand(cmds, config).run()
    assert 9 > float(time.time() - start_time) > 6
    expected_return = [[1, 1, 0], [1, 1, 0], [1, 1, 1]]

    for exp, cmd_ret in zip(expected_return, aa):
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
    password = "my$ecr3T"
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
