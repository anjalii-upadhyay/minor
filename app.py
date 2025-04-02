from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from models import db, User, Turf, Slot  # Import models from models.py
from functools import wraps
from flask import session, redirect, url_for, flash


app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///turf_booking.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)  # Initialize the database with the app


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


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email, password=password).first()
        if user:
            session['user_id'] = user.id
            session['is_owner'] = user.is_owner
            flash('Login successful!', 'success')
            return redirect(url_for('owner_dashboard' if user.is_owner else 'player_dashboard'))
        else:
            flash('Invalid credentials!', 'danger')
            return redirect(url_for('login'))
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('is_owner', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('index'))


# Owner Dashboard
@app.route('/owner/dashboard')
def owner_dashboard():
    if not is_logged_in() or not session.get('is_owner'):
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('login'))

    owner_id = session['user_id']
    turfs = Turf.query.filter_by(owner_id=owner_id).all()
    return render_template('owner_dashboard.html', turfs=turfs)

    # turfs = Turf.query.filter_by(owner_id=owner_id).all()
    # return render_template('owner_dashboard.html', turfs=turfs)


@app.route('/owner/add_turf', methods=['GET', 'POST'])
def add_turf():
    if not is_logged_in() or not session.get('is_owner'):
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



# Player Dashboard
@app.route('/player/dashboard')
def player_dashboard():
    if not is_logged_in() or session.get('is_owner'):
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('login'))

    turfs = Turf.query.all()
    return render_template('player_dashboard.html', turfs=turfs)



#book turf route

# @app.route('/player/book/<int:turf_id>', methods=['GET', 'POST'])
# def book_turf(turf_id):
#     if not is_logged_in() or session.get('is_owner'):
#         flash('Unauthorized access!', 'danger')
#         return redirect(url_for('login'))

#     turf = Turf.query.get_or_404(turf_id)
#     slots = Slot.query.filter_by(turf_id=turf_id, is_booked=False).order_by(Slot.start_time).all()

#     if request.method == 'POST':
#         selected_slots = request.form.getlist('slot_ids')  # Get selected slot IDs
#         for slot_id in selected_slots:
#             slot = Slot.query.get(slot_id)
#             if slot and not slot.is_booked:
#                 slot.is_booked = True
#                 slot.player_id = session['user_id']  # Link slot to the player
#         db.session.commit()
#         flash('Turf slots booked successfully!', 'success')
#         return redirect(url_for('player_dashboard'))

#     return render_template('book_turf.html', turf=turf, slots=slots)

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


# Database creation logic
if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create all tables in the database
        print("Database and tables created successfully!")
    app.run(debug=True)
