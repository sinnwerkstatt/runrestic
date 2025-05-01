# runrestic

<!-- [![Release](https://img.shields.io/github/v/release/sinnwerkstatt/runrestic)](https://img.shields.io/github/v/release/sinnwerkstatt/runrestic) -->
[![PyPI](https://img.shields.io/pypi/v/runrestic)](https://pypi.org/project/runrestic)
[![Build status](https://img.shields.io/github/actions/workflow/status/sinnwerkstatt/runrestic/main.yml?branch=main)](https://github.com/sinnwerkstatt/runrestic/actions/workflows/main.yml?query=branch%3Amain)
[![Commit activity](https://img.shields.io/github/commit-activity/m/sinnwerkstatt/runrestic)](https://img.shields.io/github/commit-activity/m/sinnwerkstatt/runrestic)
[![License](https://img.shields.io/github/license/sinnwerkstatt/runrestic)](https://img.shields.io/github/license/sinnwerkstatt/runrestic)

runrestic is a simple Python wrapper script for the
[Restic](https://restic.net/) backup software that initiates a backup,
prunes any old backups according to a retention policy, and validates backups
for consistency.

The script supports specifying your settings in a declarative
configuration file rather than having to put them all on the command-line, and
handles common errors.

See also [Config](config.md) and [Usage](usage.md).
