from app import create_app, db
from app.models import User, TableMetadata, CoreTable, CoreTableAssociation
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
                 permissions=json.dumps({
                     'employees': ['view', 'edit'],
                     'projects': ['view', 'edit'],
                     'departments': ['view', 'edit'],
                     'core_table': ['view', 'edit']
                 })),
            User(username='manager', accessible_tables=json.dumps(['employees', 'projects']),
                 permissions=json.dumps({
                     'employees': ['view'],
                     'projects': ['view', 'edit'],
                     'core_table': ['view']
                 })),
            User(username='employee', accessible_tables=json.dumps(['projects']),
                 permissions=json.dumps({
                     'projects': ['view'],
                     'core_table': ['view']
                 }))
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

        # Create sample data for tables
        from sqlalchemy import text

        # Employees table
        db.session.execute(text("""
            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                position TEXT
            )
        """))
        db.session.execute(text("INSERT INTO employees (name, position) VALUES ('John Doe', 'Developer'), ('Jane Smith', 'Manager'), ('Bob Johnson', 'Designer')"))

        # Projects table
        db.session.execute(text("""
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                status TEXT
            )
        """))
        db.session.execute(text("INSERT INTO projects (name, status) VALUES ('Website Redesign', 'In Progress'), ('Mobile App Development', 'Planning'), ('Database Optimization', 'Completed')"))

        # Departments table
        db.session.execute(text("""
            CREATE TABLE IF NOT EXISTS departments (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                head TEXT
            )
        """))
        db.session.execute(text("INSERT INTO departments (name, head) VALUES ('IT', 'John Smith'), ('HR', 'Emily Brown'), ('Finance', 'David Wilson')"))

        # Create core table data
        core_data = [
            CoreTable(reference_id='REF001', common_field1='Value 1', common_field2='Value A'),
            CoreTable(reference_id='REF002', common_field1='Value 2', common_field2='Value B'),
            CoreTable(reference_id='REF003', common_field1='Value 3', common_field2='Value C')
        ]
        db.session.add_all(core_data)
        db.session.flush()

        # Associate core data with table entries
        associations = [
            CoreTableAssociation(table_name='employees', table_id=1, core_id=core_data[0].id),
            CoreTableAssociation(table_name='projects', table_id=2, core_id=core_data[1].id),
            CoreTableAssociation(table_name='departments', table_id=3, core_id=core_data[2].id)
        ]
        db.session.add_all(associations)

        db.session.commit()

        print("Database seeded successfully!")

if __name__ == '__main__':
    seed_database()
