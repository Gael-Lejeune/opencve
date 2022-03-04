from flask import abort, send_file
from flask import current_app as app
from flask import flash, redirect, render_template, request, url_for
from flask_user import current_user
from opencve.commands import info
from opencve.constants import PRODUCT_SEPARATOR
from opencve.controllers.main import main, welcome
from opencve.controllers.reports import ReportController
from opencve.extensions import db
from opencve.models.changes import Change
from opencve.models.categories import Category
from opencve.models.users import User
from opencve.models.cve import Cve
from opencve.models.events import Event
from sqlalchemy import and_, or_
from sqlalchemy.dialects.postgresql import array
from sqlalchemy.orm import aliased, joinedload
from flask_login import current_user, login_required
from openpyxl import Workbook
import datetime
from opencve.forms import ActivitiesViewForm


from celery.utils.log import get_task_logger


logger = get_task_logger(__name__)


@welcome.route("/welcome")
def index():
    if not app.config.get("DISPLAY_WELCOME", False):
        abort(404)
    return render_template("index.html")


@welcome.route("/terms")
def terms():
    if not app.config.get("DISPLAY_TERMS", False):
        abort(404)
    return render_template("terms.html")


@main.route("/", methods=["GET", "POST"])
def home():
    # Allow customization of the homepage
    if not current_user.is_authenticated:
        if app.config.get("DISPLAY_WELCOME", False):
            return redirect(url_for("welcome.index"))
        return redirect(url_for("main.cves"))


    # Form used to customize the activities view
    activities_view_form = ActivitiesViewForm(
        obj=current_user,
        view=current_user.settings["activities_view"],
    )

    if request.method == "POST":
        form_name = request.form["form-name"]
        if form_name == "activities_view_form" and activities_view_form.validate():
            new_settings = {
                **current_user.settings,
                "activities_view": activities_view_form.view.data,
            }
            current_user.settings = new_settings
            db.session.commit()

            flash("Your settings has been updated.", "success")
            return redirect(url_for("main.home"))

    # For every category the user follows, we also add the products and vendors
    # Fetch the user subscriptions
    vendors = [v.name for v in current_user.vendors]
    for c in current_user.categories:
        vendors.extend([f"{v.name}" for v in c.vendors])
        vendors.extend(
            [f"{p.vendor.name}{PRODUCT_SEPARATOR}{p.name}" for p in c.products])

    # Handle the page parameter
    page = request.args.get("page", type=int, default=1)
    page = 1 if page < 1 else page
    per_page = app.config["ACTIVITIES_PER_PAGE"]

    # Only display the 5 last reports
    reports = ReportController.list_items({"user_id": current_user.id})[:5]

    # Build the query to fetch the last changes
    query = (
        Change.query.options(joinedload("cve"))
        .options(joinedload("events"))
        .filter(Change.cve_id == Cve.id)
        .filter(Change.events.any())
    )

    # Filter by subscriptions
    if current_user.settings["activities_view"] == "subscriptions":
        vendors = [v.name for v in current_user.vendors]
        vendors.extend(
            [
                f"{p.vendor.name}{PRODUCT_SEPARATOR}{p.name}"
                for p in current_user.products
            ]
        )
        for c in current_user.categories:
            vendors.extend(
                [
                    f"{v.name}" for v in c.vendors
                ]
            )
            vendors.extend(
                [
                    f"{p.vendor.name}{PRODUCT_SEPARATOR}{p.name}" for p in c.products
                ]
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
        "home.html",
        changes=changes,
        reports=reports,
        page=page,
        activities_view_form=activities_view_form,
    )

@main.route("/generateUserReport")
@login_required
def generateUserReport():
    """Generate a report for the specified user"""
    # UPLOAD_FOLDER = '/app/venv/lib/python3.7/site-packages/opencve/data/'
    # Create a xlsx file with the user name
    # The file is named after the username and the datetime
    file_name = str(current_user.username) + "_" + str(datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S"))
    wb = Workbook()
    ws = wb.active

    # Print the products of the user and the number of CVEs associated to them
    date = datetime.datetime.now() - datetime.timedelta(days=30)
    ws["A1"] = "Product"
    ws["B1"] = "Vendor"
    ws["C1"] = "Number of CVEs since" + str(date.strftime("%Y-%m-%d"))
    ws["D1"] = "CVSS2 Score mean"
    ws["E1"] = "CVSS3 Score mean"
    ws["F1"] = "Number of critical CVEs (above 7.5)"
    i = 2
    total = 0
    cves = []

    for product in current_user.products:
        # ws.append([product.name])
        ws['A'+str(i)] = product.name
        # ws.append([product.vendor.name])
        ws['B'+str(i)] = product.vendor.name
        count = 0
        cveQuery = Cve.query.filter(
            and_(
                or_(
                    # Cve.vendors.contains([product.vendor.name]) if product.vendor else None, # For the moment, the count is also based on the vendor
                    Cve.vendors.contains([product.vendor.name+'$PRODUCT$'+product.name]) if product else None,
                ),
                Cve.updated_at >= date,
            )
        )
        productCVSS2 = Cve.query.filter(
            and_(
                or_(
                    # Cve.vendors.contains([product.vendor.name]) if product.vendor else None, # For the moment, the count is also based on the vendor
                    Cve.vendors.contains([product.vendor.name+'$PRODUCT$'+product.name]) if product else None,
                ),
                Cve.updated_at >= date,
            )
        )
        cves += cveQuery
        count = cveQuery.count()
        total += count
        ws['C'+str(i)] = count
        i += 1
    ws['C'+str(i)] = total

    ws = wb.create_sheet("Vendors")
    ws["A1"] = "Vendor"
    ws["B1"] = "Number of CVEs since" + str(date.strftime("%Y-%m-%d"))
    ws["C1"] = "CVSS2 Score mean"
    ws["D1"] = "CVSS3 Score mean"
    ws["E1"] = "Number of critical CVEs (above 7.5)"
    i = 2
    total = 0
    for vendor in current_user.vendors:
        # ws.append([product.name])
        ws['A'+str(i)] = vendor.name
        # ws.append([product.vendor.name])
        count = 0
        cveQuery = Cve.query.filter(
            and_(
                or_(
                    Cve.vendors.contains([vendor.name]) if vendor else None, # For the moment, the count is also based on the vendor
                    # Cve.vendors.contains([product.vendor.name+'$PRODUCT$'+product.name]) if product else None,
                ),
                Cve.updated_at >= date,
            )
        )
        cves += cveQuery
        count = cveQuery.count()
        total += count
        ws['C'+str(i)] = count
        i += 1
    ws['C'+str(i)] = total


    # Print all the CVEs associated to the user
    # TODO: FIX. Some CVEs are selected, even if they are not associated to the user
    ws = wb.create_sheet("CVEs")
    ws['A1'] = "Creation date"
    ws['B1'] = "Last update"
    ws['C1'] = "CVE ID"
    ws['D1'] = "Vendor"
    ws['E1'] = "Product"
    ws['F1'] = "Description"
    ws['G1'] = "References"
    ws['H1'] = "CWE"
    ws['I1'] = "CVSS2"
    ws['J1'] = "CVSS3"

    i = 2
    for cve in cves:
        ws['A'+str(i)] = cve.created_at.strftime("%Y-%m-%d")
        ws['B'+str(i)] = cve.updated_at.strftime("%Y-%m-%d")
        ws['C'+str(i)] = cve.cve_id
        CVEvendors = []
        CVEproducts = []
        tab = str(cve.vendors).split('\'')
        for j in range(len(cve.vendors)):
            if tab[j] != '[' and tab[j] != ']' and ',' not in tab[j]:
                if '$' not in tab[j]: # TODO : Maybe change it to only display followed impacted vendors, or make it more easy to understand 
                    CVEvendors.append(tab[j])
                else: # TODO : Maybe change it to only display followed impacted products, or make it more easy to understand 
                    CVEproducts.append(str(cve.vendors).split('\'')[j].split('$')[2])
        ws['D'+str(i)] = str(CVEvendors)
        ws['E'+str(i)] = str(CVEproducts)
        ws['F'+str(i)] = cve.summary
        # ws['F'+str(i)] = cve.summary
        # ws['G'+str(i)] = cve.references
        # ws['H'+str(i)] = cve.cwe
        # ws['I'+str(i)] = cve.cvss2
        # ws['J'+str(i)] = cve.cvss3
        i += 1
    
    wb.save("/"+file_name+".xlsx")
    # print(os.listdir(".")) # returns list
    return send_file("/"+file_name+".xlsx", as_attachment=True, attachment_filename=file_name+".xlsx")
    

