from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

# User Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    is_owner = db.Column(db.Boolean, default=False)

    turfs = db.relationship('Turf', backref='owner', lazy=True, cascade="all, delete-orphan")
    communities_owned = db.relationship('Community', backref='owner', lazy=True, cascade="all, delete-orphan")


# Community Model
class Community(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    team_name = db.Column(db.String(100), nullable=True)  # Auto-generated if empty
    sport = db.Column(db.String(50), nullable=False)
    max_players = db.Column(db.Integer, nullable=False, default=12)
    turf_id = db.Column(db.Integer, db.ForeignKey('turf.id'), nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), default="active")  # "active" or "closed"

    turf = db.relationship('Turf', backref='communities')
    players = db.relationship('CommunityPlayers', backref='community', lazy=True, cascade="all, delete-orphan")

    __table_args__ = (db.UniqueConstraint('team_name', 'status', name='unique_active_team_name'),)

    def generate_team_name(self):
        """ Generate a team name if none is provided """
        if not self.team_name:
            self.team_name = f"Team_{self.sport}_{int(datetime.utcnow().timestamp())}"

    def save(self):
        """ Save method to auto-generate team name before committing """
        self.generate_team_name()
        db.session.add(self)
        db.session.commit()


# Community Players (Tracks Membership & Requests)
class CommunityPlayers(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    community_id = db.Column(db.Integer, db.ForeignKey('community.id'), nullable=False)
    status = db.Column(db.String(10), nullable=False, default="pending")  # "pending", "approved", "rejected"
    paid = db.Column(db.Boolean, default=False)  # Payment tracking

    __table_args__ = (db.UniqueConstraint('user_id', 'community_id', name='unique_user_community'),)

    user = db.relationship('User', backref='player_communities')


# Booking Model 
class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    community_id = db.Column(db.Integer, db.ForeignKey('community.id'), nullable=False)
    turf_id = db.Column(db.Integer, db.ForeignKey('turf.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    slot_time = db.Column(db.String(20), nullable=False)
    total_cost = db.Column(db.Float, nullable=False)  # Fetched from Turf model
    per_player_cost = db.Column(db.Float, nullable=False)  # Auto-calculated
    status = db.Column(db.String(20), default='Pending')  # "Pending", "Confirmed", "Canceled"

    community = db.relationship('Community', backref='bookings')
    owner = db.relationship('User', backref='bookings')
    turf = db.relationship('Turf', backref='bookings')

    slots = db.relationship('Slot', secondary='booking_slots', backref='bookings')

    def calculate_per_player_cost(self):
        """ Auto-calculate cost per player based on approved members """
        approved_players = CommunityPlayers.query.filter_by(community_id=self.community_id, status="approved").count()
        self.per_player_cost = self.total_cost / approved_players if approved_players > 0 else self.total_cost

    def save(self):
        """ Save method to auto-calculate cost per player before committing """
        self.calculate_per_player_cost()
        db.session.add(self)
        db.session.commit()


# Junction table for Booking and Slots
booking_slots = db.Table(
    'booking_slots',
    db.Column('booking_id', db.Integer, db.ForeignKey('booking.id')),
    db.Column('slot_id', db.Integer, db.ForeignKey('slot.id'))
)


# Slot Model
class Slot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    turf_id = db.Column(db.Integer, db.ForeignKey('turf.id'), nullable=False)
    start_time = db.Column(db.String(20), nullable=False)
    is_blocked = db.Column(db.Boolean, default=False)
    is_booked = db.Column(db.Boolean, default=False)

    turf = db.relationship('Turf', back_populates='slots')  

    def book(self):
        """ Mark slot as booked """
        self.is_booked = True
        db.session.commit()

    def unbook(self):
        """ Mark slot as available """
        self.is_booked = False
        db.session.commit()


# Turf Model
class Turf(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    price_per_hour = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text, nullable=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    slots = db.relationship('Slot', back_populates='turf', lazy=True, cascade="all, delete-orphan")


# Request to join community
class JoinRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    community_id = db.Column(db.Integer, db.ForeignKey('community.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # Status: pending, accepted, rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('join_requests', lazy=True))
    community = db.relationship('Community', backref=db.backref('join_requests', lazy=True))
