import json

from flask import request, jsonify
from flask_user import current_user, login_required

from opencve.controllers.main import main
from opencve.extensions import db
from opencve.models.products import Product
from opencve.models.vendors import Vendor
from opencve.models.categories import Category
from opencve.models import is_valid_uuid

from werkzeug.exceptions import HTTPException


@main.route("/subscriptions", methods=["POST"])
@login_required
def subscribe_to_tag():
    def _bad_request(type, id):
        return (
            jsonify({"status": "error", "message": f"{type} {id} does not exist"}),
            400,
        )

    if not current_user.is_authenticated:
        return json.dumps({"status": "error", "message": "not allowed"})

    # Check the required fields
    if not request.form["obj"] or not request.form["id"]:
        return json.dumps({"status": "error", "message": "bad request"})

    if not request.form["action"] or request.form["action"] not in [
        "subscribe",
        "unsubscribe",
    ]:
        return json.dumps({"status": "error", "message": "bad request"})

    # Vendor
    if request.form["obj"] == "vendor":
        if not is_valid_uuid(request.form["id"]):
            return _bad_request(request.form["obj"], request.form["id"])
        vendor = Vendor.query.get(request.form["id"])
        if not vendor:
            return _bad_request(request.form["obj"], request.form["id"])

        # Subscribe
        if request.form["action"] == "subscribe":
            if vendor not in current_user.vendors:
                current_user.vendors.append(vendor)
                db.session.commit()

            return json.dumps({"status": "ok", "message": "vendor added"})

        # Unsubscribe
        if request.form["action"] == "unsubscribe":
            if vendor in current_user.vendors:
                current_user.vendors.remove(vendor)
                db.session.commit()

            return json.dumps({"status": "ok", "message": "vendor removed"})

    # Category
    if request.form["obj"] == "category":
        if not is_valid_uuid(request.form["id"]):
            return _bad_request(request.form["obj"], request.form["id"])
        category = Category.query.get(request.form["id"])
        if not category:
            return _bad_request(request.form["obj"], request.form["id"])

        # Subscribe
        if request.form["action"] == "subscribe":
            if category not in current_user.categories:
                current_user.categories.append(category)
                db.session.commit()

            return json.dumps({"status": "ok", "message": "category added"})

        # Unsubscribe
        if request.form["action"] == "unsubscribe":
            if category in current_user.categories:
                current_user.categories.remove(category)
                db.session.commit()

            return json.dumps({"status": "ok", "message": "category removed"})

    # Product
    elif request.form["obj"] == "product":
        if not is_valid_uuid(request.form["id"]):
            return _bad_request(request.form["obj"], request.form["id"])
        product = Product.query.get(request.form["id"])
        if not product:
            return _bad_request(request.form["obj"], request.form["id"])

        # Subscribe
        if request.form["action"] == "subscribe":
            if product not in current_user.products:
                current_user.products.append(product)
                db.session.commit()

            return json.dumps({"status": "ok", "message": "product added"})

        # Unsubscribe
        if request.form["action"] == "unsubscribe":
            if product in current_user.products:
                current_user.products.remove(product)
                db.session.commit()

            return json.dumps({"status": "ok", "message": "product removed"})

    # Add product to a category
    if request.form["obj"] == "categoryproduct":
        category_id = request.form["id"].split("+")[0]
        product_id = request.form["id"].split("+")[1]

        if not is_valid_uuid(category_id) or not is_valid_uuid(product_id):
            return _bad_request(request.form["obj"], request.form["id"])

        category = Category.query.get(request.form["id"].split("+")[0])
        product = Product.query.get(request.form["id"].split("+")[1])

        if not product or not category:
            return _bad_request(request.form["obj"], request.form["id"])

        # Subscribe
        if request.form["action"] == "subscribe":
            if product not in category.products and category in current_user.categories:
                category.products.append(product)
                db.session.commit()

            return json.dumps({"status": "ok", "message": "product added to category"})

        # Unsubscribe
        if request.form["action"] == "unsubscribe":
            if product in category.products and category in current_user.categories:
                category.products.remove(product)
                db.session.commit()

            return json.dumps({"status": "ok", "message": "product removed from category"})

    # Add vendor to a category
    if request.form["obj"] == "categoryvendor":
        category_id = request.form["id"].split("+")[0]
        vendor_id = request.form["id"].split("+")[1]

        if not is_valid_uuid(category_id) or not is_valid_uuid(vendor_id):
            return _bad_request(request.form["obj"], request.form["id"])

        category = Category.query.get(request.form["id"].split("+")[0])
        vendor = Vendor.query.get(request.form["id"].split("+")[1])

        if not vendor or not category:
            return _bad_request(request.form["obj"], request.form["id"])

        # Subscribe
        if request.form["action"] == "subscribe":
            if vendor not in category.vendors and category in current_user.categories:
                category.vendors.append(vendor)
                db.session.commit()

            return json.dumps({"status": "ok", "message": "vendor added to category"})

        # Unsubscribe
        if request.form["action"] == "unsubscribe":
            if vendor in category.vendors and category in current_user.categories:
                category.vendors.remove(vendor)
                db.session.commit()

            return json.dumps({"status": "ok", "message": "vendor removed from category"})

    return json.dumps({"status": "error", "message": "bad request"})
