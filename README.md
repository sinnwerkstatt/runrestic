![python version](https://img.shields.io/badge/python-3.6+-blue.svg)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
![Travis (.com)](https://api.travis-ci.com/sinnwerkstatt/runrestic.svg?branch=master)
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

For a more comprehensive example see the [example.toml](https://github.com/sinnwerkstatt/runrestic/blob/master/sample/example.toml)
 or check the [schema.json](https://github.com/sinnwerkstatt/runrestic/blob/master/runrestic/runrestic/schema.json)

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
- /etc/runrestic/*example*.toml
- ~/.config/runrestic/*example*.toml

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

### Prometheus / Grafana metrics
[@d-matt](https://github.com/d-matt) created a nice dashboard for Grafana here: https://grafana.com/grafana/dashboards/11064/revisions

### systemd timer or cron

If you want to run runrestic automatically, say once a day, the you can
configure a job runner to invoke it periodically.


#### systemd

If you're using systemd instead of cron to run jobs, download the [sample systemd service file](https://raw.githubusercontent.com/sinnwerkstatt/runrestic/master/sample/systemd/runrestic.service)
and the [sample systemd timer file](https://raw.githubusercontent.com/sinnwerkstatt/runrestic/master/sample/systemd/runrestic.timer).
Then, from the directory where you downloaded them:

```bash
sudo mv runrestic.service runrestic.timer /etc/systemd/system/
sudo systemctl enable runrestic.timer
sudo systemctl start runrestic.timer
```

#### cron

If you're using cron, download the [sample cron file](https://raw.githubusercontent.com/sinnwerkstatt/runrestic/master/sample/cron/runrestic).
Then, from the directory where you downloaded it:

```bash
sudo mv runrestic /etc/cron.d/runrestic
sudo chmod +x /etc/cron.d/runrestic
```

## Changelog
* v**0.5**! Expect breaking changes.
    * metrics output is a bit different
    * see new `parallel` and `retry_*` options. 


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

# Thanks
This project was initially based on [borgmatic](https://github.com/witten/borgmatic/) but has since evolved into something else.
