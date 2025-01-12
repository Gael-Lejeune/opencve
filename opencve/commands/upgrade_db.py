from pathlib import Path

import click
from flask.cli import with_appcontext
from flask_migrate import upgrade
from flask_migrate import migrate

# from flask_migrate import current

from opencve.commands import ensure_config


@click.command()
@ensure_config
@with_appcontext
def upgrade_db():
    """Create or upgrade the database."""
    migrations_path = Path(__file__).parent.parent.resolve() / "migrations"

    print("DB initialisation check...")
    upgrade(directory=str(migrations_path))
    print()

    print("Starting migration...")
    migrate(directory=str(migrations_path))
    print()

    print("Starting upgrade...")
    upgrade(directory=str(migrations_path))
    print()
