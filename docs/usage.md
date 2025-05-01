# Runrestic usage

## Installing runrestic and restic

To install **runrestic**, run the following command to download and install it:

```bash
sudo pip3 install --upgrade runrestic
```

You can either manually download and install [Restic](https://restic.net/) or you can just run `runrestic` and it'll try to download it for you.

## Initializing and running

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

Certain `restic` flags like `--dry-run/-n` are built into `runrestic` as well and will be passed to restic where applicable.

If, however, you need to pass along arbitrary other flags you can now add them to the end of your `runrestic` call like so:

```bash
runrestic backup -- --one-file-system
```

## Logs for restic and hooks

The output of `restic` and the configured pre/post-hooks is added to the `runrestic` logs at the level defined in
`[execution] proc_log_level` (default: DEBUG), which can be overwritten with the CLI option `-p/--proc-log-level`.

For process log levels greater than `INFO` the output of file names is suppressed and for log levels greater than WARNING
`restic` is executed with the `--quiet` option. If the process log level is set to `DEBUG`, then restic is executed
with the `--verbose` option.

It is also possible to add `restic` progress messages to the logs by using the CLI option `--show-progress INTERVAL`
where the `INTERVAL` is the number of seconds between the progress messages.

## Restic shell

To use the options defined in `runrestic` with `restic` (e.g. for a backup restore), you can use the `shell` action:

```bash
runrestic shell
```

If you are using multiple repositories or configurations, you can select one now.
