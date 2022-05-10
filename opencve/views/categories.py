from asyncio.log import logger
import os
import uuid
from opencve.models.changes import Change

from celery import Celery
from sqlalchemy.orm import aliased, joinedload
from opencve.constants import PRODUCT_SEPARATOR
from sqlalchemy.dialects.postgresql import array
from flask import current_app as app
from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from opencve.models.cve import Cve
from flask_wtf import FlaskForm
from opencve.commands import info
from opencve.controllers.categories import (
    CategoryController,
    create_category,
    delete_category,
    edit_category_name,
    import_from_excel,
    generateCategoryReport,
)
from opencve.controllers.main import main
from opencve.models.categories import Category
from opencve.utils import get_categories_letters
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = "/tmp/shared/"
ALLOWED_EXTENSIONS = {"xlsx"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@login_required
@main.route("/categories", methods=["GET", "POST"])
def categories():  # Categories list
    categories, _, pagination = CategoryController.list(request.args)
    # if a category name is specified by a POST form, we create the given category
    if request.method == "POST" and request.form.get("category_name"):
        category_name = request.form.get("category_name")
        if create_category(str(category_name).lower()) == -1:
            flash(f"Category {category_name} already exists.")
        else:
            return redirect(url_for("main.categories"))

    return render_template(
        "categories.html",
        categories=categories,
        letters=get_categories_letters(),
        pagination=pagination,
        form=FlaskForm(),
    )


@main.route("/category/<category_name>")
@login_required
def category(category_name):  # Specified Category page
    category = Category.query.filter_by(name=category_name).first()

    # Handle the page parameter
    page = request.args.get("page", type=int, default=1)
    page = 1 if page < 1 else page
    per_page = app.config["ACTIVITIES_PER_PAGE"]

    # Build the query to fetch the last changes
    query = (
        Change.query.options(joinedload("cve"))
        .options(joinedload("events"))
        .filter(Change.cve_id == Cve.id)
        .filter(Change.events.any())
    )

    vendors = [v.name for v in category.vendors]
    vendors.extend([f"{v.name}" for v in category.vendors])
    vendors.extend(
        [f"{p.vendor.name}{PRODUCT_SEPARATOR}{p.name}" for p in category.products]
    )
    if not vendors:
        vendors = [None]
    query = query.filter(Cve.vendors.has_any(array(vendors)))

    # List the paginated changes
    changes = (
        query.order_by(Change.created_at.desc())
        .limit(per_page)
        .offset((page - 1) * per_page)
        .all()
    )

    return render_template(
        "category.html", changes=changes, page=page, category=category, form=FlaskForm()
    )


@login_required
@main.route("/category/<category_name>/edit", methods=["GET", "POST"])
@login_required
def edit_name(
    category_name,
):  # Specified Category page when the name modifying form is called
    category = Category.query.filter_by(name=category_name).first()
    if request.method == "POST" and request.form.get("new_category_name"):
        new_category_name = request.form.get("new_category_name")
        if edit_category_name(category, str(new_category_name).lower()) == -1:
            logger.warn("already exists")
            flash(f"Category {new_category_name} already exists.")
        else:
            return redirect(url_for("main.category", category_name=new_category_name))
    return render_template("category.html", category=category, form=FlaskForm())


@login_required
@main.route("/category/<category_name>/delete")
@login_required
def delete(category_name):  # Specified Category page when the delete button is clicked
    category = Category.query.filter_by(name=category_name).first()
    if delete_category(category) == -1:
        flash(
            f"Error while deleting the category, someone else must be subscribed to it..."
        )
    else:
        return redirect(url_for("main.categories"))


@login_required
@main.route("/category/<category_name>/upload", methods=["GET", "POST"])
@login_required
# Specified Category page when the product list uploading form is used
def upload_file(category_name):
    category = Category.query.filter_by(name=category_name).first()
    if request.method == "POST" and "file" in request.files:
        file = request.files["file"]
        # If the user does not select a file, the browser submits an empty file without a filename.
        if file.filename == "":
            flash("No selected file")
            return render_template("category.html", category=category, form=FlaskForm())
        if not allowed_file(file.filename):
            flash("File Format Not Allowed")
            return render_template("category.html", category=category, form=FlaskForm())
        if file:
            extensions = secure_filename(file.filename).split(".")[1]
            filename = str(uuid.uuid4()) + "." + str(extensions)
            app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
            path_to_file = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(path_to_file)
            file.save(secure_filename(path_to_file))
            file.close()
            if import_from_excel.delay(category.name, path_to_file) == -1:
                flash('Excel file not containing "tag" row')
            else:
                flash(
                    "File Uploaded, if the format is good and the required column is in the first three rows, the product will soon appear in the category subscriptions.\n Please keep in mind that this may take a while depending on the size of the file you uploaded."
                )
            return render_template("category.html", category=category, form=FlaskForm())
    else:
        return render_template("category.html", category=category, form=FlaskForm())


@login_required
@main.route("/category/<category_name>/generateCategoryReport", methods=["GET", "POST"])
@login_required
def generateReport(category_name):
    category = Category.query.filter_by(name=category_name).first()
    logger.debug(category)
    return generateCategoryReport(category, 30)
