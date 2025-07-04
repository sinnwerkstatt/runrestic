# See here for image contents: https://github.com/microsoft/vscode-dev-containers/tree/v0.234.0/containers/ubuntu/.devcontainer/base.Dockerfile

# [Choice] Ubuntu version (use ubuntu-22.04 or ubuntu-18.04 on local arm64/Apple Silicon): ubuntu-22.04, ubuntu-20.04, ubuntu-18.04
ARG VARIANT="noble"
FROM mcr.microsoft.com/vscode/devcontainers/base:0-${VARIANT}

# [Optional] Uncomment this section to install additional OS packages.
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends software-properties-common
# Install more python versions for testing purposes
RUN add-apt-repository ppa:deadsnakes/ppa \
    && apt-get update \
    && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends python3.10-venv python3.11-venv python3.12-venv python3.13-venv pipx

# Setup default python tools in a venv via pipx to avoid conflicts
ENV PIPX_HOME=/usr/local/py-utils \
    PIPX_BIN_DIR=/usr/local/py-utils/bin
ENV PATH=${PATH}:${PIPX_BIN_DIR}
RUN pipx install ruff
RUN pipx install isort
RUN pipx install mypy
RUN pipx install poetry
RUN pipx install pycodestyle
RUN pipx install pydocstyle
RUN pipx install pylint

# Install Python Poetry
USER vscode
# create the virtualenv in the project directory so that they are no longer ephemeral
RUN poetry config virtualenvs.in-project false
RUN poetry config virtualenvs.path ./.virtualenvs
