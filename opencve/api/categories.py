from asyncio.log import logger
from flask import request
from flask_restful import fields, marshal_with

from opencve.utils import get_cpe_list_from_specific_product
from opencve.api.base import BaseResource
from opencve.api.cves import cves_fields
from opencve.api.fields import HumanizedNameField, ProductsListField, VendorsListField
from opencve.api.vendors import vendor_list_fields
from opencve.api.products import product_fields
from opencve.controllers.cves import CveController
from opencve.controllers.categories import CategoryController
from opencve.models.categories import Category
from opencve.models.cve import Cve
from opencve.constants import PRODUCT_SEPARATOR
from sqlalchemy.dialects.postgresql import array
from sqlalchemy import and_, or_, func
import datetime




category_list_fields = {
    "name": fields.String(attribute="name"),
    "human_name": HumanizedNameField(attribute="name"),
}

category_fields = dict(
    category_list_fields, **{"products": ProductsListField(attribute="products"), "vendors": VendorsListField(attribute="vendors")},
)


class CategoryListResource(BaseResource):
    @marshal_with(category_list_fields)
    def get(self):
        return CategoryController.list_items(request.args)


class CategoryResource(BaseResource):
    @marshal_with(category_fields)
    def get(self, name):
        return CategoryController.get({"name": name})


class CategoryCveResource(BaseResource):
    @marshal_with(cves_fields)
    def get(self, name):
        period = request.args.get("period", 30)
        criticality = request.args.get("criticality", 0.0)
        date = datetime.datetime.now() - datetime.timedelta(days=int(period))
        category = CategoryController.get({"name": name})
        vendors = []
        vendors.extend(
                [
                    f"{v.name}" for v in category.vendors
                ]
            )
        for product in category.products:
            cpes = get_cpe_list_from_specific_product(product)
            vendors.extend(cpes)
        if not vendors:
            return []

        cves = Cve.query.filter(
            and_(
                Cve.vendors.has_any(array(vendors)),
                Cve.updated_at >= date,
                or_(
                    Cve.cvss2 >= float(criticality),
                    Cve.cvss3 >= float(criticality),
                )
                )
            ).order_by(Cve.updated_at.desc()).all() 

        if not cves:
            return []
        else:
            return cves

class CategoryVendorsResource(BaseResource):
    @marshal_with(vendor_list_fields)
    def get(self, name):
        category = Category.query.filter_by(
            name=name
        ).first()
        return category.vendors


class CategoryProductsResource(BaseResource):
    @marshal_with(product_fields)
    def get(self, name):
        category = Category.query.filter_by(
            name=name
        ).first()
        return category.products
