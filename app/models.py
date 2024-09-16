from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
import json
from sqlalchemy import inspect

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    accessible_tables = db.Column(db.Text, default='[]')
    permissions = db.Column(db.Text, default='{}')
    is_active = db.Column(db.Boolean, default=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        return str(self.id)

    def get_accessible_tables(self):
        return json.loads(self.accessible_tables)

    def set_accessible_tables(self, tables):
        self.accessible_tables = json.dumps(tables)

    def get_permissions(self):
        return json.loads(self.permissions)

    def set_permissions(self, permissions):
        self.permissions = json.dumps(permissions)

    def can_view(self, table_name):
        permissions = self.get_permissions()
        return table_name in permissions and 'view' in permissions[table_name]

    def can_edit(self, table_name):
        permissions = self.get_permissions()
        return table_name in permissions and 'edit' in permissions[table_name]

    def can_view_core_table(self):
        permissions = self.get_permissions()
        return 'core_table' in permissions and 'view' in permissions['core_table']

    def can_edit_core_table(self):
        permissions = self.get_permissions()
        return 'core_table' in permissions and 'edit' in permissions['core_table']

class TableMetadata(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    table_name = db.Column(db.String(64), unique=True, nullable=False)
    description = db.Column(db.String(256))

class CoreTable(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reference_id = db.Column(db.String(50), unique=True, nullable=False)
    common_field1 = db.Column(db.String(100))
    common_field2 = db.Column(db.String(100))

    @classmethod
    def get_fields(cls):
        return [column.key for column in cls.__table__.columns if column.key != 'id']

class CoreTableAssociation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    table_name = db.Column(db.String(64), nullable=False)
    table_id = db.Column(db.Integer, nullable=False)
    core_id = db.Column(db.Integer, db.ForeignKey('core_table.id'), nullable=False)
    core = db.relationship('CoreTable', backref=db.backref('associations', lazy=True))
