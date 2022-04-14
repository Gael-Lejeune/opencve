import datetime

import click
from flask import current_app as app
from flask.cli import with_appcontext
from sqlalchemy.exc import IntegrityError

from opencve.commands import ensure_config, error, info
from opencve.extensions import db
from opencve.models.categories import Category
from opencve.models.users import User
from opencve.commands import info


@click.command()
@click.argument("name")
@with_appcontext
def create_category(name):
    """Create a Category."""
    name = str(name).lower()
    if Category.query.filter_by(name=name).first():
        raise click.BadParameter(f"{name} already exists.", param_hint="name")

    category = Category(
        name=name,
    )
    db.session.add(category)
    try:
        db.session.commit()
    except IntegrityError as e:
        error(e)
    else:
        info("[CREATE_CATEGORY] Category {} created.".format(category))
