from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
import json
import uuid
from config import Config
import boto3
import os

app = Flask(__name__)
app.config.from_object(Config)

# Provide current_user to all templates
@app.context_processor
def inject_user():
    user = None
    if 'user_id' in session:
        user = JSONDatabase.get_user_by_id(session['user_id'])
    return dict(current_user=user)

# JSON Database Helper
DATA_FILE = 'sample_data.json'

class JSONDatabase:
    @staticmethod
    def load_data():
        if not os.path.exists(DATA_FILE):
            return {"photographers": [], "bookings": [], "users": []}
        try:
            with open(DATA_FILE, 'r') as f:
                data = json.load(f)
                if 'users' not in data:
                    data['users'] = []
                return data
        except json.JSONDecodeError:
            return {"photographers": [], "bookings": [], "users": []}

    @staticmethod
    def save_data(data):
        with open(DATA_FILE, 'w') as f:
            json.dump(data, f, indent=2)

    @classmethod
    def get_user_by_email(cls, email):
        data = cls.load_data()
        for u in data.get('users', []):
            if u.get('email') == email:
                return u
        return None

    @classmethod
    def get_user_by_id(cls, user_id):
        data = cls.load_data()
        for u in data.get('users', []):
            if u.get('_id') == user_id:
                return u
        return None

    @classmethod
    def insert_user(cls, user):
        data = cls.load_data()
        user['_id'] = str(uuid.uuid4())
        data.setdefault('users', []).append(user)
        cls.save_data(data)
        return user['_id']

    @classmethod
    def get_photographers(cls, query=None):
        data = cls.load_data()
        photographers = data.get('photographers', [])
        
        if not query:
            return photographers

        filtered = []
        for p in photographers:
            match = True
            
            if 'name' in query:
                search_term = query['name']['$regex'].lower()
                if search_term not in p.get('name', '').lower():
                    match = False
                    
            if 'price' in query and match:
                max_price = query['price']['$lte']
                if p.get('price', 0) > max_price:
                    match = False
                    
            if match:
                filtered.append(p)
                
        return filtered

    @classmethod
    def get_photographer(cls, photog_id):
        data = cls.load_data()
        for p in data.get('photographers', []):
            if p.get('_id') == photog_id:
                return p
        return None

    @classmethod
    def insert_photographer(cls, photographer):
        data = cls.load_data()
        photographer['_id'] = str(uuid.uuid4())
        data.setdefault('photographers', []).append(photographer)
        cls.save_data(data)
        return photographer['_id']

    @classmethod
    def update_photographer(cls, photog_id, updates):
        data = cls.load_data()
        for i, p in enumerate(data.get('photographers', [])):
            if p.get('_id') == photog_id:
                data['photographers'][i].update(updates)
                cls.save_data(data)
                return True
        return False

    @classmethod
    def delete_photographer(cls, photog_id):
        data = cls.load_data()
        original_len = len(data.get('photographers', []))
        data['photographers'] = [p for p in data.get('photographers', []) if p.get('_id') != photog_id]
        if len(data['photographers']) < original_len:
            cls.save_data(data)
            return True
        return False

    @classmethod
    def get_booking(cls, photog_id, event_date):
        data = cls.load_data()
        for b in data.get('bookings', []):
            if b.get('photographer_id') == photog_id and b.get('event_date') == event_date:
                return b
        return None

    @classmethod
    def get_bookings_by_photographer(cls, photog_id):
        data = cls.load_data()
        bookings = []
        for b in data.get('bookings', []):
            if b.get('photographer_id') == photog_id:
                bookings.append(b)
        return bookings

    @classmethod
    def insert_booking(cls, booking):
        data = cls.load_data()
        booking['_id'] = str(uuid.uuid4())
        data.setdefault('bookings', []).append(booking)
        cls.save_data(data)
        return booking['_id']

# AWS S3 client initialization
s3_client = boto3.client(
    's3',
    aws_access_key_id=app.config['AWS_ACCESS_KEY_ID'],
    aws_secret_access_key=app.config['AWS_SECRET_ACCESS_KEY'],
    region_name=app.config['AWS_REGION']
)

# Optional SES client for email confirmations
ses_client = None
if app.config.get('AWS_SES_SOURCE_EMAIL'):
    ses_client = boto3.client(
        'ses',
        aws_access_key_id=app.config['AWS_ACCESS_KEY_ID'],
        aws_secret_access_key=app.config['AWS_SECRET_ACCESS_KEY'],
        region_name=app.config['AWS_SES_REGION']
    )

# Helper function to upload a file to S3 and return the URL

def upload_to_s3(file_obj, filename):
    bucket = app.config['AWS_S3_BUCKET']
    s3_client.upload_fileobj(file_obj, bucket, filename,
                             ExtraArgs={'ACL': 'public-read'})
    url = f"https://{bucket}.s3.{app.config['AWS_REGION']}.amazonaws.com/{filename}"
    return url

# Routes

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = JSONDatabase.get_user_by_email(email)
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['_id']
            session['user_email'] = user['email']
            flash('Logged in successfully!', 'success')
            
            role = user.get('role')
            if role == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif role == 'photographer':
                return redirect(url_for('photographer_dashboard'))
            return redirect(url_for('index'))
        else:
            flash('Invalid email or password.', 'error')
            
    return render_template('login.html')

@app.route('/admin_dashboard')
def admin_dashboard():
    if 'user_id' not in session:
        flash('Please log in first.', 'error')
        return redirect(url_for('login'))
        
    user = JSONDatabase.get_user_by_id(session['user_id'])
    if not user or user.get('role') != 'admin':
        flash('Admin access restricted.', 'error')
        return redirect(url_for('index'))
        
    data = JSONDatabase.load_data()
    return render_template('admin_dashboard.html', users=data.get('users', []), photographers=data.get('photographers', []))

@app.route('/admin/delete_user/<id>', methods=['POST'])
def delete_user(id):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    current_user = JSONDatabase.get_user_by_id(session['user_id'])
    if not current_user or current_user.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403

    # Adding delete logic internally
    data = JSONDatabase.load_data()
    user_to_delete = None
    for u in data.get('users', []):
        if u.get('_id') == id:
            user_to_delete = u
            break
            
    if user_to_delete:
        # If it's a photographer, delete their linked profile too
        if user_to_delete.get('role') == 'photographer' and 'photographer_id' in user_to_delete:
            JSONDatabase.delete_photographer(user_to_delete['photographer_id'])
            
        data['users'] = [u for u in data.get('users', []) if u.get('_id') != id]
        JSONDatabase.save_data(data)
        return jsonify({'status': 'deleted'})
        
    return jsonify({'error': 'User not found'}), 404

@app.route('/photographer_dashboard')
def photographer_dashboard():
    if 'user_id' not in session:
        flash('Please log in first.', 'error')
        return redirect(url_for('login'))
        
    user = JSONDatabase.get_user_by_id(session['user_id'])
    if not user or user.get('role') != 'photographer':
        flash('Access restricted.', 'error')
        return redirect(url_for('index'))
        
    photographer = JSONDatabase.get_photographer(user.get('photographer_id'))
    bookings = JSONDatabase.get_bookings_by_photographer(user.get('photographer_id'))
    return render_template('photographer_dashboard.html', photographer=photographer, bookings=bookings)

@app.route('/update_profile', methods=['POST'])
def update_profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    user = JSONDatabase.get_user_by_id(session['user_id'])
    if not user or user.get('role') != 'photographer':
        return redirect(url_for('index'))
        
    specialization = request.form.get('specialization')
    price = request.form.get('price')
    
    try:
        price = float(price)
    except (ValueError, TypeError):
        price = 0.0

    photographer = JSONDatabase.get_photographer(user.get('photographer_id'))
    if photographer:
        JSONDatabase.update_photographer(photographer['_id'], {
            'specialization': specialization,
            'price': price
        })
        flash('Profile updated successfully!', 'success')
        
    return redirect(url_for('photographer_dashboard'))

@app.route('/upload_sample_photo', methods=['POST'])
def upload_sample_photo():
    if 'user_id' not in session:
        return redirect(url_for('login'))
        
    user = JSONDatabase.get_user_by_id(session['user_id'])
    if not user or user.get('role') != 'photographer':
        return redirect(url_for('index'))
        
    image_file = request.files.get('sample_image')
    if image_file and image_file.filename:
        # Mock upload functionality or use real S3 details based on requirements
        filename = f"samples/{uuid.uuid4()}_{image_file.filename}"
        
        try:
             url = upload_to_s3(image_file, filename)
        except Exception as e:
            # Fallback for local testing without AWS configured
            app.logger.error(f"S3 Upload failed: {e}")
            url = f"/static/uploads/{image_file.filename}"
            
            # Simple local save logic if AWS isn't fully configured
            os.makedirs(os.path.join(app.root_path, 'static', 'uploads'), exist_ok=True)
            image_file.seek(0)
            image_file.save(os.path.join(app.root_path, 'static', 'uploads', image_file.filename))

        photographer = JSONDatabase.get_photographer(user.get('photographer_id'))
        if photographer:
            samples = photographer.get('sample_photos', [])
            samples.append(url)
            JSONDatabase.update_photographer(photographer['_id'], {'sample_photos': samples})
            flash('Sample photo uploaded!', 'success')
            
    return redirect(url_for('photographer_dashboard'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        role = request.form.get('role', 'customer')

        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return redirect(url_for('register'))

        existing_user = JSONDatabase.get_user_by_email(email)
        if existing_user:
            flash('Email already registered.', 'error')
            return redirect(url_for('register'))

        user_data = {
            'name': name,
            'email': email,
            'phone': phone,
            'password_hash': generate_password_hash(password),
            'role': role
        }
        
        if role == 'photographer':
            # Create a photographer profile linked to this user's email
            photog_id = JSONDatabase.insert_photographer({
                'name': name,
                'email': email,  # Link by email for notifications
                'phone': phone,  # Add phone for SMS notifications
                'specialization': 'To be updated',
                'available_dates': [],
                'price': 0,
                'rating': 0,
                'image_url': '',
                'sample_photos': []
            })
            user_data['photographer_id'] = photog_id

        user_id = JSONDatabase.insert_user(user_data)
        
        session['user_id'] = user_id
        session['user_email'] = email
        flash('Registration successful!', 'success')
        
        if role == 'photographer':
            return redirect(url_for('photographer_dashboard'))
        return redirect(url_for('index'))

    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('user_email', None)
    flash('Logged out successfully.', 'success')
    return redirect(url_for('index'))

@app.route('/photographers')
def list_photographers():
    search = request.args.get('search')
    price_filter = request.args.get('price')
    query = {}
    if search:
        query['name'] = {'$regex': search, '$options': 'i'}
    if price_filter:
        try:
            price_val = float(price_filter)
            query['price'] = {'$lte': price_val}
        except ValueError:
            pass
            
    photographers = JSONDatabase.get_photographers(query)
    return render_template('photographers.html', photographers=photographers)

@app.route('/add_photographer', methods=['GET', 'POST'])
def add_photographer():
    if request.method == 'POST':
        name = request.form.get('name')
        specialization = request.form.get('specialization')
        available_dates = request.form.get('available_dates')
        price = float(request.form.get('price', 0))
        rating = float(request.form.get('rating', 0))
        image_file = request.files.get('image')

        image_url = ''
        if image_file and image_file.filename:
            filename = f"photographers/{image_file.filename}"
            image_url = upload_to_s3(image_file, filename)

        JSONDatabase.insert_photographer({
            'name': name,
            'specialization': specialization,
            'available_dates': available_dates.split(','),
            'price': price,
            'rating': rating,
            'image_url': image_url
        })
        flash('Photographer added successfully!')
        return redirect(url_for('list_photographers'))
    return render_template('admin.html')

@app.route('/book', methods=['POST'])
def book():
    if 'user_id' not in session:
        flash('Please log in to book a photographer.', 'error')
        return redirect(url_for('login'))

    user = JSONDatabase.get_user_by_id(session['user_id'])
    if not user:
        flash('User not found. Please log in again.', 'error')
        return redirect(url_for('login'))

    data = request.form
    photographer_id = data.get('photographer_id')
    name = data.get('name')
    email = user.get('email')
    phone = user.get('phone', 'N/A')
    event_date = data.get('event_date')
    event_type = data.get('event_type')

    # prevent duplicate booking for same photographer and date
    existing = JSONDatabase.get_booking(photographer_id, event_date)
    
    if existing:
        flash('This date is already booked for the selected photographer.', 'error')
        return redirect(request.referrer or url_for('list_photographers'))

    booking = {
        'photographer_id': photographer_id,
        'name': name,
        'email': email,
        'phone': phone,
        'event_date': event_date,
        'event_type': event_type
    }
    JSONDatabase.insert_booking(booking)

    photographer = JSONDatabase.get_photographer(photographer_id)

    # AWS SNS for Photographer Notification
    try:
        sns_client = boto3.client(
            'sns',
            aws_access_key_id=app.config['AWS_ACCESS_KEY_ID'],
            aws_secret_access_key=app.config['AWS_SECRET_ACCESS_KEY'],
            region_name=app.config['AWS_REGION']
        )
        message = f"New Booking via Capture Moments!\nClient: {name}\nDate: {event_date}\nType: {event_type}\nPhone: {phone}\nEmail: {email}"
        
        # In a real app, this would use the photographer's verified phone number or email topic
        # For demonstration, we attempt to publish, but log if it fails
        if photographer and photographer.get('email'):
            # Publishing to a topic or direct to phone requires setup in AWS console
            app.logger.info(f"Would send SNS to {photographer.get('name')} at {photographer.get('email')}: {message}")
            # sns_client.publish(PhoneNumber=photographer.get('phone'), Message=message) 
    except Exception as e:
        app.logger.error(f"SNS publish failed: {e}")

    # optionally send email if SES configured
    if ses_client:
        try:
            ses_client.send_email(
                Source=app.config['AWS_SES_SOURCE_EMAIL'],
                Destination={'ToAddresses': [email]},
                Message={
                    'Subject': {'Data': 'Booking Confirmation - Capture Moments'},
                    'Body': {
                        'Text': {'Data': f"Thank you {name}, your booking is confirmed for {event_date}."}
                    }
                }
            )
        except Exception as e:
            app.logger.error(f"SES send_email failed: {e}")

    flash('Booking confirmed!')
    return redirect(url_for('list_photographers'))

@app.route('/update_photographer/<id>', methods=['POST'])
def update_photographer(id):
    data = request.form
    fields = {}
    if 'name' in data:
        fields['name'] = data.get('name')
    if 'specialization' in data:
        fields['specialization'] = data.get('specialization')
    if 'available_dates' in data:
        fields['available_dates'] = data.get('available_dates').split(',')
    if 'price' in data:
        fields['price'] = float(data.get('price', 0))
    if 'rating' in data:
        fields['rating'] = float(data.get('rating', 0))
    if 'image' in request.files and request.files['image'].filename:
        image_file = request.files['image']
        filename = f"photographers/{image_file.filename}"
        fields['image_url'] = upload_to_s3(image_file, filename)

    JSONDatabase.update_photographer(id, fields)
    return jsonify({'status': 'success'})

@app.route('/delete_photographer/<id>', methods=['POST'])
def delete_photographer(id):
    JSONDatabase.delete_photographer(id)
    return jsonify({'status': 'deleted'})

if __name__ == '__main__':
    app.run(debug=True)
