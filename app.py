from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, Blueprint
import sqlite3
import random
import traceback
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from functools import wraps
from datetime import datetime
from models import db, User, Turf, Slot, Community, JoinRequest

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///turf_booking.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)  # Initialize the database with the app
migrate = Migrate(app, db)

community_bp = Blueprint('community', __name__)

# Helper Function to Check if User is Logged In
def is_logged_in():
    return 'user_id' in session


# Routes
@app.route('/')
def home():
    # Check if the user has seen the animation using a query parameter or session
    if 'has_seen_animation' not in session:
        return redirect(url_for('animation'))

    # If the animation has already been seen, render the index page
    return render_template('index.html')


@app.route('/animation')
def animation():
    # Render the animation page
    return render_template('animation.html')


@app.route('/index')
def index():
    return render_template('index.html')

@app.route('/set_animation_seen', methods=['POST'])
def set_animation_seen():
    session['has_seen_animation'] = True
    return '', 204  # No content response


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("You need to log in first!", "danger")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        is_owner = True if request.form.get('is_owner') == 'on' else False

        if User.query.filter_by(email=email).first():
            flash('Email already registered!', 'danger')
            return redirect(url_for('register'))

        new_user = User(username=username, email=email, password=password, is_owner=is_owner)
        db.session.add(new_user)
        db.session.commit()

        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')


# Route to Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()

        if user and user.password == password:
            session['user_id'] = user.id
            session['is_owner'] = user.is_owner
            flash("Logged in successfully!", "success")
            return redirect(url_for('player_dashboard'))  # Always go to dashboard

        flash("Invalid email or password.", "warning")

    return render_template('login.html')


# Route to Logout
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('is_owner', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('index'))


# Owner Dashboard
@app.route('/owner/dashboard')
@login_required
def owner_dashboard():
    if not session.get('is_owner'):
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('login'))

    owner_id = session['user_id']
    turfs = Turf.query.filter_by(owner_id=owner_id).all()
    return render_template('owner_dashboard.html', turfs=turfs)

    # turfs = Turf.query.filter_by(owner_id=owner_id).all()
    # return render_template('owner_dashboard.html', turfs=turfs)


@app.route('/owner/add_turf', methods=['GET', 'POST'])
@login_required
def add_turf():
    if not session.get('is_owner'):
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('login'))

    if request.method == 'POST':
        name = request.form['name']
        location = request.form['location']
        price_per_hour = float(request.form['price_per_hour'])
        description = request.form['description']

        new_turf = Turf(name=name, location=location, price_per_hour=price_per_hour, description=description,
                        owner_id=session['user_id'])
        db.session.add(new_turf)
        db.session.commit()
        create_slots_for_turf(new_turf.id) 
        flash('Turf added successfully!', 'success')
        return redirect(url_for('owner_dashboard'))
    return render_template('add_turf.html')

#helper function to create slot
def create_slots_for_turf(turf_id):
    time_slots = [
        f"{hour:02d}:00 - {hour:02d}:50" for hour in range(24)
    ]
    for start_time in time_slots:
        new_slot = Slot(turf_id=turf_id, start_time=start_time)
        db.session.add(new_slot)
    db.session.commit()


#turf details route
@app.route('/owner_dashboard/turf/<int:turf_id>', methods=['GET', 'POST'])
@login_required
def turf_details(turf_id):
    turf = Turf.query.get(turf_id)
    if not turf or turf.owner_id != session['user_id']:
        flash("Unauthorized access.", "danger")
        return redirect(url_for('owner_dashboard'))

    slots = Slot.query.filter_by(turf_id=turf_id).order_by(Slot.start_time).all()

    if request.method == 'POST':
        slot_id = request.form.get('slot_id')
        action = request.form.get('action')
        slot = Slot.query.get(slot_id)

        if slot:
            if action == 'block':
                slot.is_blocked = True
            elif action == 'unblock':
                slot.is_blocked = False
            db.session.commit()
            flash("Slot status updated successfully.", "success")
        else:
            flash("Invalid slot ID.", "danger")
        return redirect(url_for('turf_details', turf_id=turf_id))

    return render_template('turf_details.html', turf=turf, slots=slots)


@app.route('/player/book/<int:turf_id>', methods=['GET', 'POST'])
def book_turf(turf_id):
    if not is_logged_in() or session.get('is_owner'):
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('login'))

    turf = Turf.query.get_or_404(turf_id)
    slots = Slot.query.filter_by(turf_id=turf_id, is_booked=False, is_blocked=False).order_by(Slot.start_time).all()

    if request.method == 'POST':
        selected_slots = request.form.getlist('slot_ids')  # Get selected slot IDs
        if not selected_slots:  # Check if no slots are selected
            flash("You must select at least one slot to book!", "danger")
            return redirect(url_for('book_turf', turf_id=turf_id))

        booked_slots = []
        for slot_id in selected_slots:
            slot = Slot.query.get(slot_id)
            if slot and not slot.is_booked:
                slot.is_booked = True
                slot.player_id = session['user_id']  # Link slot to the player
                booked_slots.append(slot.start_time)
        db.session.commit()

        # Store confirmation data
        session['confirmation'] = {
            'turf_name': turf.name,
            'turf_location': turf.location,
            'price_per_hour': turf.price_per_hour,
            'booked_slots': booked_slots,
        }

        return redirect(url_for('booking_confirmation'))

    return render_template('book_turf.html', turf=turf, slots=slots)


@app.route('/player/confirmation')
def booking_confirmation():
    if 'confirmation' not in session:
        flash("No booking details found!", "danger")
        return redirect(url_for('player_dashboard'))

    confirmation = session.pop('confirmation')  # Retrieve and remove confirmation details
    return render_template('booking_confirmation.html', confirmation=confirmation)


#update slot status    
def update_slot_status(slot_id, is_booked, player_id=None):
    slot = Slot.query.get(slot_id)
    if slot:
        slot.is_booked = is_booked
        slot.player_id = player_id if is_booked else None
        db.session.commit()


# Route to create a community
@app.route('/create_community', methods=['POST'])
def create_community():
    data = request.get_json()

    # Extract fields from the incoming request
    team_name = data.get('team_name', '')  # Optional input
    sport = data.get('sport')
    max_players = int(data.get('max_players', 12))
    turf_id = int(data.get('turf_id'))
    owner_id = session.get('user_id')  

    if not owner_id:
        return jsonify({'error': 'User is not logged in.'}), 401  # Unauthorized if no owner_id

    status = data.get('status', 'active')

    try:
        # Auto-generate team name if not provided
        if not team_name:
            team_name = f"Team_{owner_id}_{sport}"

        new_community = Community(
            team_name=team_name,
            sport=sport,
            max_players=max_players,
            turf_id=turf_id,
            owner_id=owner_id, 
            status=status
        )

        db.session.add(new_community)
        db.session.commit()

        return jsonify({'message': 'Community created successfully!', 'team_name': new_community.team_name}), 201

    except Exception as e:
        print("Error occurred during community creation:")
        print(traceback.format_exc()) 
        return jsonify({'error': str(e)}), 500
    

# Route for Joining Community
@app.route('/join-community')
def join_community():
    communities = Community.query.all()  
    return render_template('join_community.html', communities=communities)


# Route for sending request to join community
@app.route('/send-join-request', methods=['POST'])
def send_join_request():
    user_id = session.get('user_id')
    if not user_id:
        print("User not logged in. Redirecting to login.")
        session['page_last_visited_url'] = request.referrer or url_for('join_community')
        return redirect(url_for('login'))

    community_id = request.form.get('community_id')
    print(f"Community ID received: {community_id}")
    existing_request = JoinRequest.query.filter_by(user_id=user_id, community_id=community_id).first()

    if existing_request:
        flash("You have already sent a request to this community.", "warning")
    else:
        new_request = JoinRequest(user_id=user_id, community_id=community_id, status='pending')
        db.session.add(new_request)
        db.session.commit()
        flash("Join request sent successfully!", "success")

    return redirect(url_for('join_community'))


# Route to fetch the list of communities
@app.route('/get_communities', methods=['GET'])
def get_communities():
    try:
        # Query all communities from the database
        communities = Community.query.all()

        # Convert the list of communities to a list of dictionaries
        community_list = [{
            'id': community.id,
            'team_name': community.team_name,
            'sport': community.sport,
            'max_players': community.max_players,
            'status': community.status
        } for community in communities]

        return jsonify(community_list), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Store Last Visited Webpage
@app.before_request
def page_last_visited():
    excluded_routes = ['login', 'logout', 'static', 'register']
    if request.endpoint not in excluded_routes and request.method == 'GET':
        session['page_last_visited_url'] = request.path


@app.route('/player/dashboard')
def player_dashboard():
    if 'user_id' not in session:
        flash("Please login first.", "info")
        return redirect(url_for('login'))

    turfs = Turf.query.all()  # Fetch all turfs from DB
    return render_template('player_dashboard.html', turfs=turfs)


@app.route('/my_communities')
@login_required
def my_communities():
    user_id = session['user_id']
    if not user_id:
        flash("You need to log in first!", 'warning')
        return redirect(url_for('login'))
    
    communities = Community.query.filter_by(owner_id=user_id).all()  # Assuming a Community model
    return render_template('my_communities.html', my_communities=communities)


# Database creation logic
if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create all tables in the database
        print("Database and tables created successfully!")
    print(app.url_map)
    app.run(debug=True)