from sqlalchemy_utils import UUIDType

from opencve.context import _humanize_filter
from opencve.extensions import db
from opencve.models import BaseModel, users_products, categories_products


class Product(BaseModel):
    __tablename__ = "products"

    name = db.Column(db.String(), nullable=False, index=True)

    # Relationships
    vendor_id = db.Column(UUIDType(binary=False), db.ForeignKey("vendors.id"))
    vendor = db.relationship("Vendor", back_populates="products")
    users = db.relationship("User", secondary=users_products)
    categories = db.relationship("Category", secondary=categories_products)

    product_name = db.Column(db.String(), nullable=True, index=True)
    version = db.Column(db.String(), nullable=True, index=True)
    update = db.Column(db.String(), nullable=True)
    edition = db.Column(db.String(), nullable=True)
    language = db.Column(db.String(), nullable=True)
    sw_edition = db.Column(db.String(), nullable=True)
    target_sw = db.Column(db.String(), nullable=True)
    target_hw = db.Column(db.String(), nullable=True)
    other = db.Column(db.String(), nullable=True)

    @property
    def human_name(self):
        return _humanize_filter(self.name)

    def __repr__(self):
        return "<Product {}>".format(self.name)
