![python version](https://img.shields.io/badge/python-3.7+-blue.svg)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
![Travis (.com)](https://api.travis-ci.com/sinnwerkstatt/runrestic.svg?branch=main)
![PyPI](https://img.shields.io/pypi/v/runrestic)
[![Stackshare: runrestic](https://img.shields.io/badge/stackshare-runrestic-068DFE.svg)](https://stackshare.io/runrestic)
![PyPI - Downloads](https://img.shields.io/pypi/dm/runrestic)

# Runrestic

runrestic is a simple Python wrapper script for the
[Restic](https://restic.net/) backup software that initiates a backup,
prunes any old backups according to a retention policy, and validates backups
for consistency. The script supports specifying your settings in a declarative
configuration file rather than having to put them all on the command-line, and
handles common errors.

## Example config

```toml
repositories = [
    "/tmp/restic-repo",
    "sftp:user@host:/srv/restic-repo",
    "s3:s3.amazonaws.com/bucket_name"
    ]

[environment]
RESTIC_PASSWORD = "CHANGEME"

[backup]
sources = [
    "/home",
    "/var"
    ]

[prune]
keep-last =  3
keep-hourly =  5
```

Alternatively you can also just use JSON. For a more comprehensive example see the [example.toml](https://github.com/sinnwerkstatt/runrestic/blob/main/sample/example.toml)
or check the [schema.json](https://github.com/sinnwerkstatt/runrestic/blob/main/runrestic/runrestic/schema.json)

## Getting started

### Installing runrestic and restic

To install **runrestic**, run the following command to download and install it:

```bash
sudo pip3 install --upgrade runrestic
```

<br>
You can either manually download and install [Restic](https://restic.net/) or you can just run `runrestic` and it'll try to download it for you.

### Initializing and running

Once you have `restic` and `runrestic` ready, you should put a config file in on of the scanned locations, namely:

- /etc/runrestic.toml
- /etc/runrestic/_example_.toml
- ~/.config/runrestic/_example_.toml
- /etc/runrestic.json
- /etc/runrestic/_example_.json
- ~/.config/runrestic/_example_.json

Afterwards, run

```bash
runrestic init # to initialize all the repos in `repositories`

runrestic  # without actions will do: runrestic backup prune check
# or
runrestic [action]
```

<br>
Certain `restic` flags like `--dry-run/-n` are built into `runrestic` as well and will be passed to restic where applicable.

If, however, you need to pass along arbitrary other flags you can now add them to the end of your `runrestic` call like so:

```bash
runrestic backup -- --one-file-system
```

#### Logs for restic and hooks

The output of `restic` and the configured pre/post-hooks is added to the `runrestic` logs at the level defined in
`[execution] proc_log_level` (default: DEBUG), which can be overwritten with the CLI option `-p/--proc-log-level`.

For process log levels greater than `INFO` the output of file names is suppressed and for log levels greater than WARNING
`restic` is executed with the `--quiet` option. If the process log level is set to `DEBUG`, then restic is executed
with the `--verbose` option.

It is also possible to add `restic` progress messages to the logs by using the CLI option `--show-progress INTERVAL`
where the `INTERVAL` is the number of seconds between the progress messages.

### Restic shell

To use the options defined in `runrestic` with `restic` (e.g. for a backup restore), you can use the `shell` action:

```bash
runrestic shell
```

If you are using multiple repositories or configurations, you can select one now.

### Prometheus / Grafana metrics

[@d-matt](https://github.com/d-matt) created a nice dashboard for Grafana here: https://grafana.com/grafana/dashboards/11064/revisions

### systemd timer or cron

If you want to run runrestic automatically, say once a day, the you can
configure a job runner to invoke it periodically.

#### systemd

If you're using systemd instead of cron to run jobs, download the [sample systemd service file](https://raw.githubusercontent.com/sinnwerkstatt/runrestic/main/sample/systemd/runrestic.service)
and the [sample systemd timer file](https://raw.githubusercontent.com/sinnwerkstatt/runrestic/main/sample/systemd/runrestic.timer).
Then, from the directory where you downloaded them:

```bash
sudo mv runrestic.service runrestic.timer /etc/systemd/system/
sudo systemctl enable runrestic.timer
sudo systemctl start runrestic.timer
```

#### cron

If you're using cron, download the [sample cron file](https://raw.githubusercontent.com/sinnwerkstatt/runrestic/main/sample/cron/runrestic).
Then, from the directory where you downloaded it:

```bash
sudo mv runrestic /etc/cron.d/runrestic
sudo chmod +x /etc/cron.d/runrestic
```

## Changelog

- v0.5.30
  - Fix metric setting in restic runner for "check"
  - Support Python 3.13
    - Add Python 3.13 in devcontainer so that it can be used for testing
    - Updated Poetry lock
  - Enhance test coverage
    - Modified restic tools test to use mock file operations and shortened retry times for faster test execution
- v0.5.29
  - Support Python 3.12
  - Updated devcontainer to Ubuntu 24.04 (noble)
- v0.5.28
  - Allow jsonschema >= 4.0
- v0.5.27
  - Fix output parsing for new restic version 0.14.0
  - Introduce failsafe output parser which supports default values
- v0.5.26
  - Add output messages from `restic` and pre/post-hook commands to runrestic logs.
  - New CLI argument `--show-progress INTERVAL` for the restic progress update interval in seconds (default None)
- v0.5.25
  - Drop support for Python 3.6, add support for Python 3.9 and 3.10, update dependencies
- v0.5.24
  - Exit the script with returncode = 1 if there was an error in any of the tasks
- v0.5.23
  - support JSON config files.
- v0.5.21

  - fix issue where "check" does not count towards overall "errors"-metric

- v**0.5**! Expect breaking changes.
  - metrics output is a bit different
  - see new `parallel` and `retry_*` options.

## Ansible

@tabic wrote an ansible role, you can find it here: https://github.com/outwire/ansible-role-restic . (I have neither checked nor tested it.)

## Development

This project is managed with [poetry](https://python-poetry.org/)

[Install it](https://github.com/python-poetry/poetry#installation) if not already present:

```bash
curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python
# or
pip install --user poetry
```

### Installing dependencies

```bash
poetry install
```

### Running Tests

```bash
poetry run pytest
```

### Using VScode devcontainer

The project contains a `.devcontainer` folder with the settings for VScode to [develop inside container](https://code.visualstudio.com/docs/remote/containers). The Python virtual environment
created by poetry is stored outside the container in the projects path `.virtualenvs` so that it survives container rebuilds.

The Ubuntu 24.04 based container uses Python 3.12 as system version and includes minimal Python 3.8 to 3.11 versions
for creating virtual environments in any of those versions.

It is possible to switch the Python version used by `poetry` with the command `poetry env use <version>`,
see [poetry managing environments](https://python-poetry.org/docs/managing-environments/) for more details.

# Thanks

This project was initially based on [borgmatic](https://github.com/witten/borgmatic/) but has since evolved into something else.
