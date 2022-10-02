# Standard libraries
import os
import subprocess

# Feature libraries
import toml
import click

from .. import lib


@click.group(name="jobrunner")
def jobrunner():
    """
    CLI for managing simulations jobs
    """
    pass