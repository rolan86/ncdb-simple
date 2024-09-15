from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, login_required, logout_user, current_user
from app import db
from app.models import User, TableMetadata
from sqlalchemy import inspect, Table, text
import json
import logging

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    return render_template('index.html')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    if request.method == 'POST':
        username = request.form['username'].lower()
        password = request.form['password']
        logging.info(f"Login attempt for username: {username}")
        
        user = User.query.filter_by(username=username).first()
        if user:
            logging.info(f"User found: {user.username}")
            if user.check_password(password):
                logging.info("Password check successful")
                login_user(user)
                return redirect(url_for('main.dashboard'))
            else:
                logging.info("Password check failed")
        else:
            logging.info("User not found")
        
        flash('Invalid username or password')
    return render_template('login.html')

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@bp.route('/check_user_tables')
@login_required
def check_user_tables():
    return jsonify({
        'username': current_user.username,
        'accessible_tables': current_user.get_accessible_tables(),
        'permissions': current_user.get_permissions()
    })

@bp.route('/raw_employees')
def raw_employees():
    employees = Employee.query.all()
    return jsonify([{'id': e.id, 'name': e.name, 'position': e.position} for e in employees])

@bp.route('/dashboard')
@login_required
def dashboard():
    accessible_tables = current_user.get_accessible_tables()
    table_metadata = TableMetadata.query.filter(TableMetadata.table_name.in_(accessible_tables)).all()
    user_tables = {meta.table_name: meta.description for meta in table_metadata}
    return render_template('dashboard.html', tables=user_tables)

@bp.route('/get_table_data/<table_name>')
@login_required
def get_table_data(table_name):
    logging.info(f"Attempting to fetch data for table: {table_name}")
    logging.info(f"User {current_user.username} accessible tables: {current_user.get_accessible_tables()}")
    
    if table_name not in current_user.get_accessible_tables():
        logging.warning(f"Access denied for user {current_user.username} to table {table_name}")
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        inspector = inspect(db.engine)
        if table_name not in inspector.get_table_names():
            logging.error(f"Table not found in database: {table_name}")
            return jsonify({'error': 'Table not found'}), 404

        table = Table(table_name, db.metadata, autoload_with=db.engine)
        columns = [column.name for column in table.columns]
        
        result = db.session.execute(table.select()).fetchall()
        logging.info(f"Fetched {len(result)} rows from {table_name}")
        
        data = []
        for row in result:
            row_dict = {col: getattr(row, col) for col in columns}
            data.append({
                'id': row_dict['id'],
                'user_data': json.dumps({k: str(v) for k, v in row_dict.items() if k != 'id'})
            })

        logging.info(f"Returning {len(data)} rows of data for {table_name}")
        return jsonify(data)
    except Exception as e:
        logging.error(f"Error fetching data for {table_name}: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/seed_sample_data')
def seed_sample_data():
    try:
        with db.engine.connect() as connection:
            # Create sample tables
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS employees (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    position TEXT
                )
            """))
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS projects (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    status TEXT
                )
            """))
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS departments (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    head TEXT
                )
            """))

            # Seed sample data
            connection.execute(text("INSERT INTO employees (name, position) VALUES ('John Doe', 'Developer'), ('Jane Smith', 'Manager'), ('Bob Johnson', 'Designer')"))
            connection.execute(text("INSERT INTO projects (name, status) VALUES ('Website Redesign', 'In Progress'), ('Mobile App Development', 'Planning'), ('Database Optimization', 'Completed')"))
            connection.execute(text("INSERT INTO departments (name, head) VALUES ('IT', 'John Smith'), ('HR', 'Emily Brown'), ('Finance', 'David Wilson')"))

            connection.commit()

        # Add table metadata
        for table_name in ['employees', 'projects', 'departments']:
            if not TableMetadata.query.filter_by(table_name=table_name).first():
                meta = TableMetadata(table_name=table_name, description=f"{table_name.capitalize()} Information")
                db.session.add(meta)

        db.session.commit()
        return jsonify({'message': 'Sample data and metadata seeded successfully'}), 200
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error seeding sample data: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/update_table_data/<table_name>', methods=['POST'])
@login_required
def update_table_data(table_name):
    if not current_user.can_edit(table_name):
        return jsonify({'error': 'Access denied'}), 403
    
    data = request.json
    table = db.metadata.tables.get(table_name)
    if not table:
        return jsonify({'error': 'Table not found'}), 404

    user_data = json.loads(data['user_data'])
    
    if data['id']:
        # Update existing row
        stmt = table.update().where(table.c.id == data['id']).values(**user_data)
        db.session.execute(stmt)
    else:
        # Insert new row
        stmt = table.insert().values(**user_data)
        db.session.execute(stmt)

    db.session.commit()
    return jsonify({'success': True})

@bp.route('/test_users')
def test_users():
    users = User.query.all()
    user_list = [{"id": user.id, "username": user.username, "password_hash": user.password_hash} for user in users]
    return jsonify(user_list)

