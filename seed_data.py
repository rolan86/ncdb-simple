from app import create_app, db
from app.models import User, TableMetadata
import json

def seed_database():
    app = create_app()
    with app.app_context():
        # Clear existing data
        db.drop_all()
        db.create_all()

        # Create users
        users = [
            User(username='admin', accessible_tables=json.dumps(['employees', 'projects', 'departments']),
                 permissions=json.dumps({'employees': ['view', 'edit'], 'projects': ['view', 'edit'], 'departments': ['view', 'edit']})),
            User(username='manager', accessible_tables=json.dumps(['employees', 'projects']),
                 permissions=json.dumps({'employees': ['view'], 'projects': ['view', 'edit']})),
            User(username='employee', accessible_tables=json.dumps(['projects']),
                 permissions=json.dumps({'projects': ['view']}))
        ]

        for user in users:
            user.set_password('password')
            db.session.add(user)

        # Create table metadata
        table_metadata = [
            TableMetadata(table_name='employees', description='Employee Information'),
            TableMetadata(table_name='projects', description='Project Details'),
            TableMetadata(table_name='departments', description='Department Information')
        ]
        db.session.add_all(table_metadata)

        db.session.commit()

        print("Database seeded successfully!")

if __name__ == '__main__':
    seed_database()
