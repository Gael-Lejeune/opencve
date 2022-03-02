import datetime

import click
from flask import current_app as app
from flask.cli import with_appcontext
from sqlalchemy.exc import IntegrityError

from opencve.commands import ensure_config, error, info
from opencve.extensions import db
from opencve.models.categories import Category
from opencve.models.products import Product
from opencve.models.vendors import Vendor


@click.command()
@click.argument("category")
@click.argument("vendor")
@click.argument("product")
@with_appcontext
def add_product_to_category(category, vendor, product):
    """Add Product to category"""
    category_query = Category.query.filter_by(name=category).first().id
    if not category_query:
        raise click.BadParameter(
            f"{category} does not exists in Categories", param_hint="category")
    print(category_query)
    vendor_query = Vendor.query.filter_by(name=vendor).first().id
    if not vendor_query:
        raise click.BadParameter(
            f"{vendor} does not exists in Vendors", param_hint="vendor")
    print(vendor_query)
    product_query = Product.query.filter_by(
        name=product, vendor_id=vendor_query).first().id
    if not product_query:
        raise click.BadParameter(
            f"{product} does not exists in Products", param_hint="product")
    print(product_query)

    db.session.execute("INSERT INTO categories_products(category_id,product_id) VALUES (('" +
                       str(category_query)+"'),('"+str(product_query)+"'))")

    try:
        db.session.commit()
    except IntegrityError as e:
        error(e)
    else:
        info("[ADD_PRODUCT_TO_CATEGORY] Product " +
             str(product)+" added to category "+str(category))
