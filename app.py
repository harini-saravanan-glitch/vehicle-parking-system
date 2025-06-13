from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from models import db, User, ParkingLot, Booking,ParkingSpot,Reservation
from flask import session
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///parking.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key'

db.init_app(app)

with app.app_context():
    db.create_all()
    existing_admin = User.query.filter_by(username='admin').first()
    if not existing_admin:
        admin = User(
            username='admin',
            passhash=generate_password_hash('admin'),
            name='Admin User',  
            is_admin=True,
            created_at=datetime.utcnow()
        )
        db.session.add(admin)
        db.session.commit()



@app.route('/')
def home():
    if session.get('user_id'):
        if session.get('is_admin'):
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('user_dashboard'))
    return redirect(url_for('login'))



@app.route('/user/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()
        if user and user.verify_password(password):
            session['user_id'] = user.id
            session['is_admin'] = user.is_admin
            return redirect(url_for('admin_dashboard' if user.is_admin else 'user_dashboard'))
        else:
            flash('Invalid credentials!')
            return redirect(url_for('login'))

    return render_template("login.html")


@app.route('/user/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        if User.query.filter_by(username=username).first():
            flash('Username already exists.')
            return redirect(url_for('register'))

        new_user = User(username=username, name=email, is_admin=False)
        new_user.password = password

        db.session.add(new_user)
        db.session.commit()
        flash('Registered successfully! Please login.')
        return redirect(url_for('login'))

    return render_template("register.html")


@app.route('/user/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        return f"Password reset link sent to {email} (simulated)."
    return render_template("forgot_password.html")


@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully.")
    return redirect(url_for('login'))



def is_admin():
    return session.get('is_admin') is True
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()
        if user and user.verify_password(password) and user.is_admin:
            session['user_id'] = user.id
            session['is_admin'] = True
            flash('Welcome Admin!')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid admin credentials!')
            return redirect(url_for('admin_login'))

    return render_template("admin_login.html")

@app.route('/admin/promote/<int:user_id>', methods=['POST'])
def promote_user(user_id):
    if not is_admin():
        flash("Unauthorized access.")
        return redirect(url_for('login'))

    user = User.query.get_or_404(user_id)
    if user.is_admin:
        flash(f"{user.username} is already an admin.")
    else:
        user.is_admin = True
        db.session.commit()
        flash(f"{user.username} has been promoted to admin.")

    return redirect(url_for('admin_users'))

@app.route('/admin/create-admin', methods=['GET', 'POST'])
def create_admin():
    if not is_admin():
        flash("Unauthorized access.")
        return redirect(url_for('login'))

    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        if User.query.filter_by(username=username).first():
            flash("Username already exists.")
            return redirect(url_for('create_admin'))

        new_admin = User(username=username, name=email, is_admin=True)
        new_admin.password = password
        db.session.add(new_admin)
        db.session.commit()

        flash("New admin account created successfully.")
        return redirect(url_for('admin_users'))

    return render_template("create_admin.html")
