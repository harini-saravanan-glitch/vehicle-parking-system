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





@app.route('/admin/dashboard')
def admin_dashboard():
    if not is_admin():
        flash("Unauthorized access.")
        return redirect(url_for('login'))

    first_lot = ParkingLot.query.first() 
    return render_template("admin_dashboard.html", first_lot=first_lot)



@app.route('/admin/add-parking', methods=['GET', 'POST'])
def add_parking():
    if not is_admin():
        flash("Unauthorized access.")
        return redirect(url_for('login'))

    if request.method == 'POST':
        return redirect(url_for('admin_dashboard'))
    return render_template("add_parking_lot.html")

@app.route('/admin/edit-parking/<int:lot_id>', methods=['GET', 'POST'])
def edit_parking(lot_id):
    if not is_admin():
        flash("Unauthorized access.")
        return redirect(url_for('login'))

    lot = ParkingLot.query.get_or_404(lot_id)

    if request.method == 'POST':
        lot.prime_location_name = request.form['prime_location_name']
        lot.price_per_hour = request.form['price_per_hour']
        lot.address = request.form['address']
        lot.pin_code = request.form['pin_code']
        lot.max_spots = request.form['max_spots']
        db.session.commit()
        flash("Parking lot updated successfully!")
        return redirect(url_for('view_parking_lots'))

    return render_template('edit_parking.html', lot=lot)

@app.route('/admin/delete-parking/<int:lot_id>', methods=['POST', 'GET'])
def delete_parking(lot_id):
    lot = ParkingLot.query.get_or_404(lot_id)
    db.session.delete(lot)
    db.session.commit()
    flash('Parking lot deleted successfully.', 'success')
    return redirect(url_for('view_parking_lots'))




@app.route('/admin/create-parking', methods=['POST'])
def create_parking():
    if not is_admin():
        flash("Unauthorized access.")
        return redirect(url_for('login'))

    parking_lot = ParkingLot(
        prime_location_name=request.form["prime_location_name"],
        price_per_hour=request.form["price_per_hour"],
        address=request.form["address"],
        pin_code=request.form["pin_code"],
        max_spots=int(request.form["max_spots"]),
        spots_filled=0
    )

    db.session.add(parking_lot)
    db.session.commit()

    for i in range(parking_lot.max_spots):
        spot = ParkingSpot(
            lot_id=parking_lot.id,
            status='A' 
        )
        db.session.add(spot)

    db.session.commit()

    flash("Parking lot and spots created successfully!")
    return redirect(url_for('admin_dashboard'))


from flask import request

@app.route('/admin/view-parking')
def view_parking_lots():
    q = request.args.get('q', '').strip()
    
    if q:
        parking_lots = ParkingLot.query.filter(
            (ParkingLot.prime_location_name.ilike(f'%{q}%')) | 
            (ParkingLot.pin_code.ilike(f'%{q}%'))
        ).all()
    else:
        parking_lots = ParkingLot.query.all()

    return render_template('view_parking_lots.html', parking_lots=parking_lots)


@app.route('/admin/users')
def admin_users():
    if not is_admin():
        flash("Unauthorized access.")
        return redirect(url_for('login'))

    users = User.query.all()
    return render_template('admin_users.html', users=users)


@app.route('/admin/reports')
def admin_reports():
    if not is_admin():
        flash("Unauthorized access.")
        return redirect(url_for('login'))

    users = User.query.all()
    admins = [u for u in users if u.is_admin]
    total_bookings = Booking.query.count()
    total_lots = ParkingLot.query.count()

    return render_template('admin_reports.html',
                           total_users=len(users),
                           total_admins=len(admins),
                           total_lots=total_lots,
                           total_bookings=total_bookings)


@app.route('/admin/view_spots/<int:lot_id>', methods=['GET', 'POST'])
def admin_view_spots(lot_id):
    if not is_admin():
        flash("Unauthorized access.")
        return redirect(url_for('login'))

    lot = ParkingLot.query.get_or_404(lot_id)
    spots = ParkingSpot.query.filter_by(lot_id=lot_id).all()

    filled_count = ParkingSpot.query.filter_by(lot_id=lot_id, status='O').count()
    actual_spot_count = len(spots)

    return render_template(
        'admin_view_spots.html',
        lot=lot,
        spots=spots,
        filled_count=filled_count,
        actual_spot_count=actual_spot_count
    )



@app.route('/admin/toggle-spot/<int:spot_id>', methods=['POST'])
def toggle_spot_status(spot_id):
    if not is_admin():
        flash("Unauthorized access.")
        return redirect(url_for('login'))

    spot = ParkingSpot.query.get_or_404(spot_id)
    lot = spot.lot  

    if spot.status == 'A':
        spot.status = 'O'
        lot.spots_filled += 1
    elif spot.status == 'O':
        spot.status = 'A'
        if lot.spots_filled > 0:
            lot.spots_filled -= 1

    db.session.commit()
    flash(f"Spot {spot.id} status updated.")
    return redirect(url_for('admin_view_spots', lot_id=lot.id))


@app.route('/admin/delete-spot/<int:spot_id>', methods=['POST'])
def delete_spot(spot_id):
    if not is_admin():
        flash("Unauthorized access.")
        return redirect(url_for('login'))

    spot = ParkingSpot.query.get_or_404(spot_id)
    lot = spot.lot 

  
    if spot.status == 'O' and lot.spots_filled > 0:
        lot.spots_filled -= 1

    db.session.delete(spot)
    db.session.commit()

    flash(f"Spot {spot.id} deleted.")
    return redirect(url_for('admin_view_spots', lot_id=lot.id))


if __name__ == '__main__':
    app.run(debug=True)

