"""Test log output for sub-processes

Using pytest-subprocess plugin https://pytest-subprocess.readthedocs.io/
"""

import logging
import subprocess
from io import StringIO

from runrestic.restic import tools


def test_log_messages_no_output():
    """Test log messages with no output"""
    # Create a fake process object
    fake_proc = type("FakeProc", (), {})()
    fake_proc.stdout = StringIO("    ")
    assert tools.log_messages(fake_proc, "test_cmd") == ""


def test_restic_logs(caplog, fp, monkeypatch):  # pylint: disable=invalid-name
    cmd = ["restic", "-r", "test_repo", "backup"]
    out = [
        "using parent snapshot b601066b",
        "Files:           5 new,    42 changed,  1842 unmodified",
        "Dirs:            1 new,     4 changed,   103 unmodified",
        "Added to the repo: 43 MiB",
        "processed 1888 files, 11.342 GiB in 0:00",
        "snapshot 1e3c30a1 saved",
    ]
    fp.register(
        cmd,
        stdout=out,
        returncode=0,
    )
    monkeypatch.setattr(tools, "Popen", subprocess.Popen)
    caplog.set_level(logging.INFO)
    result = tools.retry_process(
        cmd,
        config={},
    )
    assert result["output"] == [(0, "\n".join([*out, ""]))]
    for log in out:
        assert log in caplog.text
    assert caplog.record_tuples[0] == (
        "runrestic.restic.tools",
        20,
        "[restic] using parent snapshot b601066b",
    )
    assert caplog.record_tuples[-1] == (
        "runrestic.restic.tools",
        20,
        "[restic] snapshot 1e3c30a1 saved",
    )


def test_restic_abort(caplog, fp, monkeypatch):  # pylint: disable=invalid-name
    cmd = ["restic", "-r", "test_repo", "backup"]
    out = ["Fatal: wrong password"]
    # Register 3 calls failing
    fp.register(cmd, stdout=out, returncode=1, occurrences=3)
    monkeypatch.setattr(tools, "Popen", subprocess.Popen)
    caplog.set_level(logging.INFO)
    result = tools.retry_process(
        cmd, config={"retry_count": 2}, abort_reasons=["Fatal: wrong password"]
    )
    assert result["output"] == [(1, "\n".join([*out, ""]))]
    assert (
        "runrestic.restic.tools",
        logging.CRITICAL,
        "[restic] Fatal: wrong password",
    ) in caplog.record_tuples
    assert (
        "runrestic.restic.tools",
        logging.ERROR,
        "Aborting 'restic' because of ['Fatal: wrong password']",
    ) in caplog.record_tuples


def test_retry_pass_logs(caplog, fp, monkeypatch):  # pylint: disable=invalid-name
    cmd = ["restic", "-r", "test_repo", "backup"]
    out_fail = ["Fatal: something went wrong"]
    out_pass = ["snapshot 1e3c30a1 saved"]
    retries = 2
    # Register #'retries' calls failing
    fp.register(cmd, stdout=out_fail, returncode=1, occurrences=retries)
    # Register final call success
    fp.register(cmd, stdout=out_pass, returncode=0)
    monkeypatch.setattr(tools, "Popen", subprocess.Popen)
    caplog.set_level(logging.INFO)
    result = tools.retry_process(
        cmd, config={"retry_count": retries}, abort_reasons=["Fatal: wrong password"]
    )
    assert result["output"] == [(1, out_fail[0] + "\n")] * retries + [
        (0, out_pass[0] + "\n")
    ]
    assert (
        "runrestic.restic.tools",
        logging.CRITICAL,
        "[restic] Fatal: something went wrong",
    ) in caplog.record_tuples
    assert (
        "runrestic.restic.tools",
        logging.INFO,
        f"Retry {retries}/{retries + 1} command 'restic'",
    ) in caplog.record_tuples


def test_retry_fail_logs(caplog, fp, monkeypatch):  # pylint: disable=invalid-name
    cmd = ["restic", "-r", "test_repo", "backup"]
    out_fail = ["Fatal: something went wrong"]
    out_pass = ["snapshot 1e3c30a1 saved"]
    retries = 3
    # Register 2 calls failing
    fp.register(cmd, stdout=out_fail, returncode=1, occurrences=retries + 1)
    # Register 3rd call success
    fp.register(cmd, stdout=out_pass, returncode=0)
    monkeypatch.setattr(tools, "Popen", subprocess.Popen)
    caplog.set_level(logging.INFO)
    result = tools.retry_process(
        cmd, config={"retry_count": retries}, abort_reasons=["Fatal: wrong password"]
    )
    assert result["output"] == [(1, out_fail[0] + "\n")] * (retries + 1)
    assert (
        "runrestic.restic.tools",
        logging.CRITICAL,
        "[restic] Fatal: something went wrong",
    ) in caplog.record_tuples
    assert (
        "runrestic.restic.tools",
        logging.INFO,
        f"Retry 2/{retries + 1} command 'restic'",
    ) in caplog.record_tuples


def test_log_level_mapping(caplog, fp, monkeypatch):  # pylint: disable=invalid-name
    cmd = ["restic", "-r", "test_repo", "backup"]
    test_messages = {
        "Random log message, not an ERROR": logging.INFO,
        "unchanged /debug/log/message": logging.DEBUG,
        "warning: restic had some issue": logging.WARNING,
        "ERROR log message upper": logging.ERROR,
        "Error: log message mix": logging.ERROR,
        "FATAL as critical message": logging.CRITICAL,
        "CRITICAL log message": logging.CRITICAL,
    }
    fp.register(cmd, stdout=list(test_messages.keys()), returncode=1, occurrences=3)
    monkeypatch.setattr(tools, "Popen", subprocess.Popen)
    caplog.set_level(logging.DEBUG)

    result = tools.retry_process(
        cmd,
        config={},
    )
    assert result["output"][-1] == (1, "\n".join(test_messages.keys()) + "\n")
    for message, level in test_messages.items():
        assert (
            "runrestic.restic.tools",
            level,
            f"[restic] {message}",
        ) in caplog.record_tuples


def test_hook_log(caplog, fp, monkeypatch):  # pylint: disable=invalid-name
    cmd = "hook_cmd --some-option 123 -v"
    test_messages = {
        "Random log message, not an ERROR": logging.INFO,
        "unchanged /debug/log/message": logging.DEBUG,
        "warning: hook cmd had some issue": logging.WARNING,
        "ERROR log message upper": logging.ERROR,
        "Error: log message mix": logging.ERROR,
        "FATAL as critical message": logging.CRITICAL,
        "CRITICAL log message": logging.CRITICAL,
    }
    fp.register(cmd, stdout=list(test_messages.keys()), returncode=0, occurrences=1)
    monkeypatch.setattr(tools, "Popen", subprocess.Popen)
    caplog.set_level(logging.DEBUG)

    result = tools.retry_process(
        cmd,
        config={},
    )
    assert result["output"] == [(0, "\n".join(test_messages.keys()) + "\n")]
    for message, level in test_messages.items():
        assert (
            "runrestic.restic.tools",
            level,
            f"[{cmd.split(' ', maxsplit=1)[0]}] {message}",
        ) in caplog.record_tuples
