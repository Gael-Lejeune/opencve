import os

import click

from opencve import __version__
from opencve.commands.celery import celery
from opencve.commands.create_user import create_user
from opencve.commands.init import init
from opencve.commands.upgrade_db import upgrade_db
from opencve.commands.imports import import_data
from opencve.commands.imports import import_data_light
from opencve.commands.webserver import webserver
from opencve.commands.create_category import create_category
from opencve.commands.create_table import create_table
from opencve.commands.add_product_to_category import add_product_to_category
from opencve.commands.read_excel import read_excel


@click.group()
@click.version_option(version=__version__)
def cli():
    """CVE Alerting Platform"""
    os.environ["FLASK_APP"] = "opencve.app:app"


cli.add_command(celery)
cli.add_command(create_user)
cli.add_command(import_data)
cli.add_command(init)
cli.add_command(upgrade_db)
cli.add_command(webserver)
cli.add_command(create_category)
cli.add_command(create_table)
cli.add_command(add_product_to_category)
cli.add_command(read_excel)
cli.add_command(import_data_light)
