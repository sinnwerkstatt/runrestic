import os
import time

from runrestic.restic.tools import (
    retry_process,
    run_multiple_commands,
    initialize_environment,
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


def test_run_multiple_commands_parallel(tmpdir):
    cmds = [
        ["python", "tests/retry_testing_tool.py", "3", "l", tmpdir],
        ["python", "tests/retry_testing_tool.py", "2", "m", tmpdir],
        ["python", "tests/retry_testing_tool.py", "1", "n", tmpdir],
    ]
    config = {"retry_count": 2, "parallel": True, "retry_backoff": "0:01"}
    start_time = time.time()
    aa = run_multiple_commands(cmds, config)
    assert 3 > time.time() - start_time > 2
    expected_return = {0: [1, 1, 0], 1: [1, 0], 2: [0]}

    for cmd_id, cmd_ret in aa.items():
        assert [x[0] for x in cmd_ret["output"]] == expected_return[cmd_id]

    cmds = [
        ("alpha", ["python", "tests/retry_testing_tool.py", "1", "aa", tmpdir]),
        ("beta", ["python", "tests/retry_testing_tool.py", "1", "ab", tmpdir]),
        ("gamma", ["python", "tests/retry_testing_tool.py", "1", "ac", tmpdir]),
    ]
    config = {"retry_count": 0, "parallel": True}
    aa = run_multiple_commands(cmds, config)
    expected_return = {"alpha": [0], "beta": [0], "gamma": [0]}

    for cmd_id, cmd_ret in aa.items():
        assert [x[0] for x in cmd_ret["output"]] == expected_return[cmd_id]


def test_run_multiple_commands_serial(tmpdir):
    cmds = [
        ["python", "tests/retry_testing_tool.py", "3", "o", tmpdir],
        ["python", "tests/retry_testing_tool.py", "3", "p", tmpdir],
        ["python", "tests/retry_testing_tool.py", "4", "q", tmpdir],
    ]
    config = {"retry_count": 2, "parallel": False, "retry_backoff": "0:01"}
    start_time = time.time()
    aa = run_multiple_commands(cmds, config)
    assert 9 > float(time.time() - start_time) > 6
    expected_return = {0: [1, 1, 0], 1: [1, 1, 0], 2: [1, 1, 1]}

    for cmd_id, cmd_ret in aa.items():
        assert [x[0] for x in cmd_ret["output"]] == expected_return[cmd_id]


def test_initialize_environment():
    env = {"TEST123": "xyz"}
    os.environ["HOME"] = ""
    assert os.environ.get("HOME") == ""
    initialize_environment(env)
    assert os.environ.get("TEST123") == "xyz"
    assert os.environ.get("XDG_CACHE_HOME") == "/var/cache"
