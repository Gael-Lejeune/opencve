import openpyxl
from pathlib import Path
from opencve.commands.add_product_to_category import add_product_to_category
import click
from flask import current_app as app
from flask.cli import with_appcontext
from sqlalchemy.exc import IntegrityError
from opencve.commands import ensure_config, error, info

from opencve.extensions import db
from opencve.models.categories import Category
from opencve.models.products import Product
from opencve.models.vendors import Vendor


def add_product(category, vendor, product):
    """Add Product to category"""
    category_query = Category.query.filter_by(name=category).first().id
    if not category_query:
        return info(f"[ADD_PRODUCT] {category} does not exists in Categories")
    vendor_query = Vendor.query.filter_by(name=vendor).first().id
    if not vendor_query:
        return info(f"[ADD_PRODUCT] {vendor} does not exists in Vendors")
    product_query = (
        Product.query.filter_by(name=product, vendor_id=vendor_query).first().id
    )
    if not product_query:
        return info(f"[ADD_PRODUCT] {product} does not exists in Products")
    # FOR TESTING ONLY, NEED TO CHECK THE INPUT OR CHANGE THE USED METHOD //TODO
    existance = db.session.execute(
        "SELECT 1 FROM categories_products WHERE category_id=('"
        + str(category_query)
        + "') and product_id=('"
        + str(product_query)
        + "')"
    ).first()
    if existance:
        return info(f"[ADD_PRODUCT] {product} already exists in category {category}")
    db.session.execute(
        "INSERT INTO categories_products(category_id,product_id) VALUES (('"
        + str(category_query)
        + "'),('"
        + str(product_query)
        + "'))"
    )
    try:
        db.session.commit()
    except IntegrityError as e:
        error(e)
    else:
        return info(
            "[ADD_PRODUCT] Product "
            + str(product)
            + " added to category "
            + str(category)
        )


@click.command()
@click.argument("category")
@click.argument("file_path")
@with_appcontext
def read_excel(category, file_path):
    xlsx_file = Path(file_path)
    wb_obj = openpyxl.load_workbook(xlsx_file)
    sheet = wb_obj.active
    l = sheet.max_row
    data = []
    for i in range(3, l):
        if sheet["G" + str(i)].value != None:
            d = (
                str(sheet["C" + str(i)].value).lower()
                + ":"
                + str(sheet["G" + str(i)].value).lower()
            )
            if d not in data:
                data.append(d)
    for i in data:
        add_product(category, i.split(":")[0], i.split(":")[1])
