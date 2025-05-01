# Runrestic configuration

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

## Scheduled execution

If you want to run runrestic automatically, say once a day, the you can
configure a job runner to invoke it periodically.

### systemd

If you're using systemd instead of cron to run jobs, download the [sample systemd service file](https://raw.githubusercontent.com/sinnwerkstatt/runrestic/main/sample/systemd/runrestic.service)
and the [sample systemd timer file](https://raw.githubusercontent.com/sinnwerkstatt/runrestic/main/sample/systemd/runrestic.timer).
Then, from the directory where you downloaded them:

```console
sudo mv runrestic.service runrestic.timer /etc/systemd/system/
sudo systemctl enable runrestic.timer
sudo systemctl start runrestic.timer
```

### cron

If you're using cron, download the [sample cron file](https://raw.githubusercontent.com/sinnwerkstatt/runrestic/main/sample/cron/runrestic).
Then, from the directory where you downloaded it:

```bash
sudo mv runrestic /etc/cron.d/runrestic
sudo chmod +x /etc/cron.d/runrestic
```

## Prometheus / Grafana metrics

[@d-matt](https://github.com/d-matt) created a nice dashboard for Grafana here: https://grafana.com/grafana/dashboards/11064/revisions

## Ansible

@tabic wrote an Ansible role, you can find it here: https://github.com/outwire/ansible-role-restic . (I have neither checked nor tested it.)
