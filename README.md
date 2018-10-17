# Overview

runrestic is a simple Python wrapper script for the
[Restic](https://restic.net/) backup software that initiates a backup,
prunes any old backups according to a retention policy, and validates backups
for consistency. The script supports specifying your settings in a declarative
configuration file rather than having to put them all on the command-line, and
handles common errors.

Here's an example config file:

```toml
repositories = [
    "/tmp/restic-repo",
    "sftp:user@host:/srv/restic-repo",
    "s3:s3:s3.amazonaws.com/bucket_name"
    ]

[environment]
RESTIC_PASSWORD = "CHANGEME"
# or RESTIC_PASSWORD_FILE = "/path/to/file"
# see https://restic.readthedocs.io/en/latest/040_backup.html#environment-variables 
# especially if you need to set environment variables like AWS_ACCESS_KEY_ID and such

[location]
source_directories = [
    "/home",
    "/var"
    ]

# exclude_patterns = []
# exclude_files = []
# https://restic.readthedocs.io/en/stable/040_backup.html#including-and-excluding-files

[retention]
keep-last =  3
keep-hourly =  5
keep-weekly = 10
keep-monthly = 30
# https://restic.readthedocs.io/en/latest/060_forget.html#removing-snapshots-according-to-a-policy

[consistency]
checks = ["check-unused", "read-data"]
# https://restic.readthedocs.io/en/stable/045_working_with_repos.html#checking-a-repo-s-integrity-and-consistency

[metrics.prometheus]
path = "/var/lib/node_exporter/textfile_collector/runrestic.prom"
```


# Getting started

To get up and running, first [install Restic](https://restic.net/#installation). 

To install runrestic, run the following command to download and install it:

```bash
sudo pip3 install --upgrade runrestic
```

Note that your pip binary may have a different name than `pip3`. Make sure
you're using Python 3, as runrestic does not support Python 2.

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

# Autopilot

If you want to run runrestic automatically, say once a day, the you can
configure a job runner to invoke it periodically.

### cron

If you're using cron, download the [sample cron file](https://raw.githubusercontent.com/andreasnuesslein/runrestic/master/sample/cron/runrestic).
Then, from the directory where you downloaded it:

```bash
sudo mv runrestic /etc/cron.d/runrestic
sudo chmod +x /etc/cron.d/runrestic
```


### systemd

If you're using systemd instead of cron to run jobs, download the [sample systemd service file](https://raw.githubusercontent.com/andreasnuesslein/runrestic/master/sample/systemd/runrestic.service)
and the [sample systemd timer file](https://raw.githubusercontent.com/andreasnuesslein/runrestic/master/sample/systemd/runrestic.timer).
Then, from the directory where you downloaded them:

```bash
sudo mv runrestic.service runrestic.timer /etc/systemd/system/
sudo systemctl enable runrestic.timer
sudo systemctl start runrestic.timer
```


# Thanks
Much of this project is copy and paste from [borgmatic](https://github.com/witten/borgmatic/).
