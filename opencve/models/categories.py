from opencve.context import _humanize_filter
from opencve.extensions import db
from opencve.models import BaseModel, categories_vendors, categories_products, users_categories


class Category(BaseModel):
    __tablename__ = "categories"

    name = db.Column(db.String(), nullable=False, unique=True)

    # Relationships
    vendors = db.relationship("Vendor", secondary=categories_vendors)
    products = db.relationship("Product", secondary=categories_products)
    users = db.relationship("User", secondary=users_categories)

    @property
    def human_name(self):
        return _humanize_filter(self.name)

    def __repr__(self):
        return "<Category {}>".format(self.name)
