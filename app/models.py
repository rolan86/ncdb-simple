from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
import json

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

class TableMetadata(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    table_name = db.Column(db.String(64), unique=True, nullable=False)
    description = db.Column(db.String(256))

