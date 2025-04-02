from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# User Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    is_owner = db.Column(db.Boolean, default=False)
    turfs = db.relationship('Turf', backref='owner', lazy=True)


# Turf Model
class Turf(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    price_per_hour = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text, nullable=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    slots = db.relationship('Slot', backref='turf', lazy=True)


# Booking Model
class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    turf_id = db.Column(db.Integer, db.ForeignKey('turf.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    slot_time = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), default='Pending')  # Pending, Confirmed, Canceled
    user = db.relationship('User', backref='bookings')
    turf = db.relationship('Turf', backref='bookings')


# Slot Model
class Slot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    turf_id = db.Column(db.Integer, db.ForeignKey('turf.id'), nullable=False)
    start_time = db.Column(db.String(20), nullable=False)
    is_blocked = db.Column(db.Boolean, default=False)
    booking_id = db.Column(db.Integer, db.ForeignKey('booking.id'), nullable=True)  # Optional if not booked
    booking = db.relationship('Booking', backref='slots')
    is_booked = db.Column(db.Boolean, default=False)
    player_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
