import string

from nested_lookup import nested_lookup
from difflib import HtmlDiff

from opencve.constants import PRODUCT_SEPARATOR
from opencve.models.cwe import Cwe
from opencve.commands import error, info, timed_operation
from opencve.extensions import db
from opencve.models.products import Product
from sqlalchemy import and_, or_, String



def check_cpe_values():
    with timed_operation("Checking wrong or missing product values..."):
        wrong_cpes = Product.query.filter(
            Product.product_name.is_(None)
            | Product.version.is_(None)
            | Product.update.is_(None)
            | Product.edition.is_(None)
            | Product.language.is_(None)
            | Product.sw_edition.is_(None)
            | Product.target_sw.is_(None)
            | Product.target_hw.is_(None)
            | Product.other.is_(None)
        ).all()
    if wrong_cpes:
        with timed_operation("Inserting missing values..."):
            for cpe in wrong_cpes:
                cpe_tab = cpe.name.split(":")
                cpe.product_name = cpe_tab[4]
                cpe.version = cpe_tab[5]
                cpe.update = cpe_tab[6]
                cpe.edition = cpe_tab[7]
                cpe.language = cpe_tab[8]
                cpe.sw_edition = cpe_tab[9]
                cpe.target_sw = cpe_tab[10]
                cpe.target_hw = cpe_tab[11]
                cpe.other = cpe_tab[12]
            db.session.commit()

def get_cpe_list_from_specific_product(product):
    regex_version = product.version.replace("*", "%")
    regex_update = product.update.replace("*", "%")
    regex_edition = product.edition.replace("*", "%")
    regex_language = product.language.replace("*", "%")
    regex_sw_edition = product.sw_edition.replace("*", "%")
    regex_target_sw = product.target_sw.replace("*", "%")
    regex_target_hw = product.target_hw.replace("*", "%")
    regex_other = product.other.replace("*", "%")

    query = Product.query.filter(
        and_(
            Product.vendor == product.vendor,
            Product.product_name == product.product_name,
            and_(
                or_(
                    Product.version.cast(String).ilike(regex_version),
                    Product.version == "*",
                ),
                or_(
                    Product.update.cast(String).ilike(regex_update),
                    Product.update == "*",
                ),
                or_(
                    Product.edition.cast(String).ilike(regex_edition),
                    Product.edition == "*",
                ),
                or_(
                    Product.language.cast(String).ilike(regex_language),
                    Product.language == "*",
                ),
                or_(
                    Product.sw_edition.cast(String).ilike(regex_sw_edition),
                    Product.sw_edition == "*",
                ),
                or_(
                    Product.target_sw.cast(String).ilike(regex_target_sw),
                    Product.target_sw == "*",
                ),
                or_(
                    Product.target_hw.cast(String).ilike(regex_target_hw),
                    Product.target_hw == "*",
                ),
                or_(
                    Product.other.cast(String).ilike(regex_other),
                    Product.other == "*",
                ),
            )
        ),
    )
    cpe_list = []
    cpe_list = [f"{cpe.vendor.name}{PRODUCT_SEPARATOR}{cpe.name}" for cpe in query.all()]
    return cpe_list

def convert_cpes(conf):
    """
    This function takes an object, extracts its CPE uris and transforms them into
    a dictionnary representing the vendors with their associated products.
    """
    uris = nested_lookup("cpe23Uri", conf) if not isinstance(conf, list) else conf

    # Create a list of tuple (vendor, product)
    cpes_t = list(set([(uri.split(":")[3], uri) for uri in uris]))

    # Transform it into nested dictionnary
    cpes = {}
    for vendor, product in cpes_t:
        if vendor not in cpes:
            cpes[vendor] = []
        cpes[vendor].append(product)

    return cpes


def flatten_vendors(vendors):
    """
    Takes a list of nested vendors and products and flat them.
    """
    data = []
    for vendor, products in vendors.items():
        data.append(vendor)
        for product in products:
            data.append(f"{vendor}{PRODUCT_SEPARATOR}{product}")
    return data


def get_cwes(problems):
    """
    Takes a list of problems and return the CWEs ID.
    """
    return list(set([p["value"] for p in problems]))


def get_cwes_details(problems):
    """
    Takes a list of problems and return the CWEs along
    with the name of the vulnerability.
    """
    cwes = {}
    for cwe_id in get_cwes(problems):
        cwes[cwe_id] = None
        cwe = Cwe.query.filter_by(cwe_id=cwe_id).first()
        if cwe:
            cwes[cwe_id] = cwe.name
    return cwes


def get_vendors_letters():
    """
    Returns a list of letters used to filter the vendors.
    """
    return list(string.ascii_lowercase + "@" + string.digits)

def get_categories_letters():
    """
    Returns a list of letters used to filter the vendors.
    """
    return list(string.ascii_lowercase + "@" + string.digits)

class CustomHtmlHTML(HtmlDiff):
    def __init__(self, *args, **kwargs):
        self._table_template = """
        <table class="table table-diff table-condensed">
            <thead>
                <tr>
                    <th colspan="2">Old JSON</th>
                    <th colspan="2">New JSON</th>
                </tr>
            </thead>
            <tbody>%(data_rows)s</tbody>
        </table>"""
        super().__init__(*args, **kwargs)

    def _format_line(self, side, flag, linenum, text):
        text = text.replace("&", "&amp;").replace(">", "&gt;").replace("<", "&lt;")
        text = text.replace(" ", "&nbsp;").rstrip()
        return '<td class="diff_header">%s</td><td class="break">%s</td>' % (
            linenum,
            text,
        )
