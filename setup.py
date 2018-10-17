from setuptools import setup, find_packages

from runrestic import __version__

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='runrestic',
    version=__version__,
    description='A wrapper script for Restic backup software that inits, creates, prunes and checks backups',
    long_description=long_description,
    long_description_content_type="text/markdown",
    author='Andreas Nüßlein',
    author_email='nuts@noova.de',
    url='https://github.com/andreasnuesslein/runrestic',
    classifiers=(
        'Development Status :: 3 - Alpha',
        'Environment :: Console',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python',
        'Topic :: Security :: Cryptography',
        'Topic :: System :: Archiving :: Backup',
    ),
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'runrestic = runrestic.commands.runrestic:main',
        ]
    },
    install_requires=(
        'toml>=0.10.0',
        'setuptools',
    ),
    include_package_data=True,
)
