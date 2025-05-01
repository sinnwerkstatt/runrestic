![python version](https://img.shields.io/badge/python-3.10+-blue.svg)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/psf/ruff)
[![PyPI](https://img.shields.io/pypi/v/runrestic)](https://pypi.org/project/runrestic)
[![Stackshare: runrestic](https://img.shields.io/badge/stackshare-runrestic-068DFE.svg)](https://stackshare.io/runrestic)
![PyPI - Downloads](https://img.shields.io/pypi/dm/runrestic)

# Runrestic

runrestic is a simple Python wrapper script for the
[Restic](https://restic.net/) backup software that initiates a backup,
prunes any old backups according to a retention policy, and validates backups
for consistency.

The script supports specifying your settings in a declarative
configuration file rather than having to put them all on the command-line, and
handles common errors.

- **Github repository**: <https://github.com/sinnwerkstatt/runrestic/>
- **Documentation**:  <!-- https://sinnwerkstatt.github.io/runrestic/ -->
  - [Usage](./docs/usage.md)
  - [Configuration](./docs/config.md)

## Changelog

- v0.5.31
  - Change project setup based on [fpgmaas/cookiecutter-uv](https://github.com/fpgmaas/cookiecutter-uv)
    - Uses `uv` as a replacement for `pip` and `ruff` instead of `black`.
    - `tox` to easily test multiple python versions
  - Drop support for Python 3.9 since it will be EOL end 2025.
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

## Development

### 1. Clone repository

Clone the repository (or fork) and change to the cloned folder.

### 2. Set Up Your Development Environment

Then, install the environment and the pre-commit hooks with

```console
make install
```

This will also generate your `uv.lock` file

### 3. Run the pre-commit hooks

Initially, the CI/CD pipeline might be failing due to formatting issues. To resolve those run:

```console
uv run pre-commit run -a
```

### 4. Check you changes before committing them

Run the checks to verify formatting and typing:

```console
make check
```

Run the defines test cases:

```console
make test
```

Generate and verify the documentation locally:

```console
make docs
```

### 5. Configure CI/CD

The CI/CD pipeline will be triggered when you open a pull request, merge to main, or when you create a new release.

To finalize the set-up for publishing to PyPI, see [here](https://fpgmaas.github.io/cookiecutter-uv/features/publishing/#set-up-for-pypi).
For activating the automatic documentation with MkDocs, see [here](https://fpgmaas.github.io/cookiecutter-uv/features/mkdocs/#enabling-the-documentation-on-github).
To enable the code coverage reports, see [here](https://fpgmaas.github.io/cookiecutter-uv/features/codecov/).

## Releasing a new version

- Create an API Token on [PyPI](https://pypi.org/).
- Add the API Token to your projects secrets with the name `PYPI_TOKEN` by visiting [this page](https://github.com/sinnwerkstatt/runrestic/settings/secrets/actions/new).
- Create a [new release](https://github.com/sinnwerkstatt/runrestic/releases/new) on Github.
- Create a new tag in the form `*.*.*`.

For more details, see [here](https://fpgmaas.github.io/cookiecutter-uv/features/cicd/#how-to-trigger-a-release).

---

Repository initiated with [fpgmaas/cookiecutter-uv](https://github.com/fpgmaas/cookiecutter-uv).
