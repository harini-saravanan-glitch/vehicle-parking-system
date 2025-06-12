from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

# ---------------- USER MODEL ----------------
class User(db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), unique=True, nullable=False)
    passhash = db.Column(db.String(128), nullable=False)
    name = db.Column(db.String(64), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    reservations = db.relationship('Reservation', backref='user', cascade="all, delete-orphan")
    bookings = db.relationship('Booking', backref='user', cascade="all, delete-orphan")

    @property
    def password(self):
        raise AttributeError("Password is not readable.")

    @password.setter
    def password(self, password):
        self.passhash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.passhash, password)

    def has_active_reservation(self):
        return any(res.leaving_timestamp is None for res in self.reservations)

    def has_active_booking(self):
        return any(booking.end_time is None for booking in self.bookings)

    def __repr__(self):
        return f"<User {self.id} - {self.username} - Admin: {self.is_admin}>"

# ---------------- PARKING LOT MODEL ----------------
class ParkingLot(db.Model):
    __tablename__ = 'parking_lot'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    prime_location_name = db.Column(db.String(128), nullable=False)
    price_per_hour = db.Column(db.Float, nullable=False)
    address = db.Column(db.String(256), nullable=False)
    pin_code = db.Column(db.String(10), nullable=False)
    max_spots = db.Column(db.Integer, nullable=False)
    spots_filled = db.Column(db.Integer, nullable=False, default=0)  # <-- Added here

    spots = db.relationship('ParkingSpot', backref='lot', cascade="all, delete-orphan")
    bookings = db.relationship('Booking', backref='parking_lot', lazy=True)

    def available_spots(self):
        return self.max_spots - self.spots_filled

    def has_available_spot(self):
        return self.spots_filled < self.max_spots

    def __repr__(self):
        return f"<ParkingLot {self.id} - {self.prime_location_name}>"


# ---------------- PARKING SPOT MODEL ----------------
class ParkingSpot(db.Model):
    __tablename__ = 'parking_spot'

    id = db.Column(db.Integer, primary_key=True)
    lot_id = db.Column(db.Integer, db.ForeignKey('parking_lot.id'), nullable=False)
    status = db.Column(db.String(1), default='A')  # A = Available, O = Occupied

    reservations = db.relationship('Reservation', backref='spot', cascade="all, delete-orphan")

    def is_available(self):
        return self.status == 'A'

    def __repr__(self):
        return f"<ParkingSpot {self.id} in Lot {self.lot_id} - Status: {self.status}>"

# ---------------- RESERVATION MODEL ----------------
class Reservation(db.Model):
    __tablename__ = 'reservation'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    spot_id = db.Column(db.Integer, db.ForeignKey('parking_spot.id'), nullable=False)
    parking_timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    leaving_timestamp = db.Column(db.DateTime, nullable=True)
    price_per_hour = db.Column(db.Float, nullable=False)

    def is_active(self):
        return self.leaving_timestamp is None

    def duration_in_hours(self):
        if not self.leaving_timestamp:
            return 0
        duration = self.leaving_timestamp - self.parking_timestamp
        return max(1, round(duration.total_seconds() / 3600))

    def calculate_total_price(self):
        return self.duration_in_hours() * self.price_per_hour

    def __repr__(self):
        return f"<Reservation {self.id} - User {self.user_id} - Spot {self.spot_id}>"

# ---------------- BOOKING MODEL ----------------
class Booking(db.Model):
    __tablename__ = 'booking'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    parking_lot_id = db.Column(db.Integer, db.ForeignKey('parking_lot.id'), nullable=False)

    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime, nullable=True)

    # ⬇️ Optionally add a price cache column if you want to store price at booking time
    # price_per_hour = db.Column(db.Float, nullable=True)

    def is_active(self):
        return self.end_time is None

    def duration_hours(self):
        if not self.end_time:
            return 0
        delta = self.end_time - self.start_time
        return max(1, round(delta.total_seconds() / 3600))  # Minimum 1 hour

    def calculate_price(self):
        return self.duration_hours() * self.parking_lot.price_per_hour

    def __repr__(self):
        return f"<Booking {self.id} - User {self.user_id} - Lot {self.parking_lot_id}>"
    




