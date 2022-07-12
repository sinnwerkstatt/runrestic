from argparse import Namespace
import os

import pytest
from toml import TomlDecodeError

from runrestic.runrestic.configuration import (
    cli_arguments,
    configuration_file_paths,
    parse_configuration,
    possible_config_paths,
)


def test_cli_arguments():
    assert cli_arguments([]) == (
        Namespace(actions=[], config_file=None, dry_run=False, log_level="info"),
        [],
    )
    assert cli_arguments(["-l", "debug"]) == (
        Namespace(actions=[], config_file=None, dry_run=False, log_level="debug"),
        [],
    )
    assert cli_arguments(["backup"]) == (
        Namespace(
            actions=["backup"], config_file=None, dry_run=False, log_level="info"
        ),
        [],
    )
    assert cli_arguments(["backup", "--", "--one-file-system"]) == (
        Namespace(
            actions=["backup"], config_file=None, dry_run=False, log_level="info"
        ),
        ["--one-file-system"],
    )
    with pytest.raises(SystemExit):
        cli_arguments(["-h"])


@pytest.fixture
def restic_dir(tmpdir):
    os.environ["XDG_CONFIG_HOME"] = str(tmpdir)
    return tmpdir.mkdir("runrestic")


@pytest.fixture
def restic_minimal_good_conf(restic_dir):
    p = restic_dir.join("example.toml")
    content = (
        'repositories = ["/tmp/restic-repo-1"]\n'
        "[environment]\n"
        'RESTIC_PASSWORD = "CHANGEME"\n'
        "[backup]\n"
        'sources = ["/etc"]\n'
        "[prune]\n"
        "keep-last = 10"
    )
    p.write(content)
    os.chmod(p, 0o0600)
    return p


@pytest.fixture
def restic_minimal_broken_conf(restic_dir):
    p = restic_dir.join("example.toml")
    content = '[environment\nRESTIC_PASSWORD = {CHANGEME"'
    p.write(content)
    os.chmod(p, 0o0600)
    return p


def test_possible_config_paths(tmpdir):
    os.environ["XDG_CONFIG_HOME"] = str(tmpdir)
    assert possible_config_paths() == [
        "/etc/runrestic.toml",
        "/etc/runrestic.json",
        "/etc/runrestic/",
        f"{tmpdir}/runrestic/",
    ]


def test_configuration_file_paths(restic_minimal_good_conf):
    paths = list(configuration_file_paths())
    assert paths == [restic_minimal_good_conf]


def test_configuration_file_paths_wrong_perms(caplog, restic_dir):
    bad_perms_file = restic_dir.join("example.toml")
    bad_perms_file.write("irrelevant")
    os.chmod(bad_perms_file, 0o0644)
    paths = list(configuration_file_paths())
    assert paths == []
    assert f"NOT using {bad_perms_file}." in caplog.text
    assert "File permissions are too open (0644)" in caplog.text


def test_parse_configuration_good_conf(restic_minimal_good_conf):
    assert parse_configuration(restic_minimal_good_conf) == {
        "name": "example.toml",
        "repositories": ["/tmp/restic-repo-1"],
        "environment": {"RESTIC_PASSWORD": "CHANGEME"},
        "execution": {"exit_on_error": True, "parallel": False, "retry_count": 0},
        "backup": {"sources": ["/etc"]},
        "prune": {"keep-last": 10},
    }


def test_parse_configuration_broken_conf(caplog, restic_minimal_broken_conf):
    with pytest.raises(TomlDecodeError):
        parse_configuration(restic_minimal_broken_conf)


#
# def test_parse_configuration_broken_conf(restic_minimal_broken_conf):
#     with pytest.raises(jsonschema.exceptions.ValidationError):
#         parse_configuration(restic_minimal_broken_conf)
