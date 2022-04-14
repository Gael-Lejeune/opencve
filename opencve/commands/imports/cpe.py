from cmath import log
import gzip
from io import BytesIO
import xml.etree.ElementTree

import requests
from cpe import CPE

from opencve.commands import header, info, timed_operation
from opencve.extensions import db
from opencve.models import get_uuid
from opencve.models.products import Product
from opencve.models.vendors import Vendor
from asyncio.log import logger

from opencve.utils import check_cpe_values


NVD_CPE_URL = (
    "https://nvd.nist.gov/feeds/xml/cpe/dictionary/official-cpe-dictionary_v2.3.xml.gz"
)


def get_slug(vendor, product=None):
    slug = vendor
    if product:
        slug += "-{}".format(product)
    return slug


def run(mappings):
    """
    Import the Vendors and Products list.
    """
    header("Importing CPE list...")

    # Download the XML file
    with timed_operation("Downloading {}...".format(NVD_CPE_URL)):
        resp = requests.get(NVD_CPE_URL).content

    # Parse the XML elements
    with timed_operation("Parsing XML elements..."):
        raw = gzip.GzipFile(fileobj=BytesIO(resp))
        del resp
        items = set()
        for _, elem in xml.etree.ElementTree.iterparse(raw):
            if elem.tag.endswith("cpe23-item"):
                items.add(elem.get("name"))
            elem.clear()
        del raw

    # Create the objects
    with timed_operation("Creating list of mappings..."):
        for item in items:
            obj = CPE(item)
            vendor = obj.get_vendor()[0]
            product = item
            # product_tab = product.split(":")

            if vendor not in mappings["vendors"].keys():
                mappings["vendors"][vendor] = dict(id=get_uuid(), name=vendor)

            if get_slug(vendor, product) not in mappings["products"].keys():
                mappings["products"][get_slug(vendor, product)] = dict(
                    id=get_uuid(),
                    name=product,
                    vendor_id=mappings["vendors"][vendor]["id"],
                    # product_name=product[4],
                    # version=product_tab[5],
                    # update=product_tab[6],
                    # edition=product_tab[7],
                    # language=product_tab[8],
                    # sw_edition=product_tab[9],
                    # target_sw=product_tab[10],
                    # target_hw=product_tab[11],
                    # other=product_tab[12],
                )
        del items

    # Insert the objects in database
    with timed_operation("Inserting Vendors and Products..."):
        db.session.bulk_insert_mappings(Vendor, mappings["vendors"].values())
        db.session.bulk_insert_mappings(Product, mappings["products"].values())
        db.session.commit()

    check_cpe_values()

    info(
        "{} vendors and {} products imported.".format(
            len(mappings["vendors"]), len(mappings["products"])
        )
    )
    del mappings
