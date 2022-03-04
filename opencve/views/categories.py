from asyncio.log import logger
import os
import uuid

from flask import current_app as app
from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from flask_wtf import FlaskForm
from opencve.commands import info
from opencve.controllers.categories import (CategoryController, create_category,
                                         delete_category, edit_category_name,
                                         read_excel, generateCategoryReport)
from opencve.controllers.main import main
from opencve.models.categories import Category
from opencve.utils import get_categories_letters
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = '/app/venv/lib/python3.7/site-packages/opencve/data'
ALLOWED_EXTENSIONS = {'xlsx'}


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@login_required
@main.route("/categories", methods=['GET', 'POST'])
def categories():  # Categories list
    categories, _, pagination = CategoryController.list(request.args)
    # if a category name is specified by a POST form, we create the given category
    if request.method == 'POST' and request.form.get('category_name'):
        category_name = request.form.get('category_name')
        if create_category(str(category_name).lower()) == -1:
            flash(f"Category {category_name} already exists.")
        else:
            return redirect(url_for('main.categories'))

    return render_template(
        "categories.html",
        categories=categories,
        letters=get_categories_letters(),
        pagination=pagination,
        form=FlaskForm()
    )


@main.route("/category/<category_name>")
@login_required
def category(category_name):  # Specified Category page
    category = Category.query.filter_by(name=category_name).first()

    return render_template(
        "category.html",
        category=category,
        form=FlaskForm()
    )


@main.route("/category/<category_name>/edit", methods=['GET', 'POST'])
@login_required
def edit_name(category_name):  # Specified Category page when the name modifying form is called
    category = Category.query.filter_by(name=category_name).first()
    if request.method == 'POST' and request.form.get('new_category_name'):
        new_category_name = request.form.get('new_category_name')
        if edit_category_name(category, str(new_category_name).lower()) == -1:
            flash(f"Category {new_category_name} already exists.")
        else:
            return redirect(url_for('main.category', category_name=new_category_name))
    else:
        return render_template(
            "category.html",
            category=category,
            form=FlaskForm()
        )


@main.route("/category/<category_name>/delete")
@login_required
def delete(category_name):  # Specified Category page when the delete button is clicked
    category = Category.query.filter_by(name=category_name).first()
    if delete_category(category) == -1:
        flash(f"Error while deleting the category, someone else must be subscribed to it...")
    else:
        return redirect(url_for('main.categories'))


@main.route("/category/<category_name>/upload", methods=['GET', 'POST'])
@login_required
# Specified Category page when the product list uploading form is used
def upload_file(category_name):
    category = Category.query.filter_by(name=category_name).first()
    if request.method == 'POST' and 'file' in request.files:
        file = request.files['file']
        # If the user does not select a file, the browser submits an empty file without a filename.
        if file.filename == '':
            flash('No selected file')
            return render_template(
                "category.html",
                category=category,
                form=FlaskForm()
            )
        if not allowed_file(file.filename):
            flash('File Format Not Allowed')
            return render_template(
                "category.html",
                category=category,
                form=FlaskForm()
            )
        if file:
            extensions = secure_filename(file.filename).split(".")[1]
            filename = str(uuid.uuid4())+"."+str(extensions)
            app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
            path_to_file = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            # file.save(secure_filename(path_to_file))
            if read_excel(category, file) == -1:
                flash(
                    'Excel file not containing "vendor", "product", "version" and "tag" rows')
            else:
                flash(f'File Uploaded and products added to category {category}')
            return redirect(request.url)
    else:
        return render_template(
            "category.html",
            category=category,
            form=FlaskForm()
        )

@main.route("/category/<category_name>/generateCategoryReport", methods=['GET', 'POST'])
@login_required
def generateReport(category_name):
    category = Category.query.filter_by(name=category_name).first()
    logger.debug(category)
    return generateCategoryReport(category, 30)