from flask import render_template, request
from flask_user import current_user
from opencve.controllers.main import main
from opencve.controllers.products import ProductController
from opencve.models.categories import Category


@main.route("/vendors/<vendor>/products")
def products(vendor):
    products, _, pagination = ProductController.list({**request.args, "vendor": vendor})
    return render_template(
        "products.html",
        products=products,
        vendor=vendor,
        pagination=pagination,
    )
