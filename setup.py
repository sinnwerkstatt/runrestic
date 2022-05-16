# This file is only here for legacy reasons.

import os.path

from setuptools import setup

here = os.path.abspath(os.path.dirname(__file__))
readme_path = os.path.join(here, "README.md")

setup(
    long_description=open(readme_path, "r", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    name="runrestic",
    version="0.5.26",
    description="A wrapper script for Restic backup software that inits, creates, prunes and checks backups",
    python_requires=">=3.7.0",
    project_urls={
        "homepage": "https://github.com/sinnwerkstatt/runrestic",
        "repository": "https://github.com/sinnwerkstatt/runrestic",
    },
    author="Andreas Nüßlein",
    author_email="andreas@nuessle.in",
    license="GPL-3.0+",
    keywords="backup",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: System Administrators",
        "Programming Language :: Python",
        "Topic :: Security :: Cryptography",
        "Topic :: System :: Archiving :: Backup",
    ],
    entry_points={
        "console_scripts": ["runrestic = runrestic.runrestic.runrestic:runrestic"]
    },
    packages=[
        "runrestic",
        "runrestic.metrics",
        "runrestic.restic",
        "runrestic.runrestic",
    ],
    package_data={"runrestic.runrestic": ["*.json"]},
    install_requires=[
        "jsonschema>=3.0,<4.0",
        "requests>=2.27.1,<3.0.0",
        "toml>=0.10,<0.11",
    ],
)
