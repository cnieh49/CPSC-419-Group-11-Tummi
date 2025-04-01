from flask import Flask, render_template, request, jsonify, redirect, url_for, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from models import db, User
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import requests

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
app.config['JWT_SECRET_KEY'] = 'jwt-secret'
app.config['UPLOAD_FOLDER'] = './uploads'

db.init_app(app)
jwt = JWTManager(app)

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    restaurant_name = db.Column(db.String(120), nullable=False)
    location = db.Column(db.String(120), nullable=False)
    notes = db.Column(db.Text, nullable=True)
    photo_url = db.Column(db.String(255), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

with app.app_context():
    db.create_all()

@app.route('/')
def home():
    return redirect(url_for('login_page'))

@app.route('/login-page')
def login_page():
    return render_template('login.html')

@app.route('/register-page')
def register_page():
    return render_template('register.html')

@app.route('/dashboard')
@jwt_required()
def dashboard():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    return jsonify({
        "email": user.email,
        "message": f"Welcome to Tummi, {user.email}!"
    })

@app.route('/user-reviews')
@jwt_required()
def user_reviews():
    user_id = get_jwt_identity()
    reviews = Review.query.filter_by(user_id=user_id).order_by(Review.timestamp.desc()).all()
    return jsonify([{
        'id': r.id,
        'restaurant_name': r.restaurant_name,
        'location': r.location,
        'notes': r.notes,
        'photo_url': r.photo_url,
        'timestamp': r.timestamp.strftime("%Y-%m-%d %H:%M:%S")
    } for r in reviews])

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/dashboard-page')
def dashboard_page():
    return render_template('dashboard.html')

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(email=data['email']).first()
    if user and user.check_password(data['password']):
        token = create_access_token(identity=user.id)
        return jsonify({'access_token': token}), 200
    return jsonify({'message': 'Invalid credentials'}), 401

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'message': 'Email already exists'}), 409
    user = User(email=data['email'])
    user.set_password(data['password'])
    db.session.add(user)
    db.session.commit()
    return jsonify({'message': 'User registered successfully'}), 201

@app.route('/add-review', methods=['POST'])
@jwt_required()
def add_review():
    user_id = get_jwt_identity()
    restaurant_name = request.form.get('restaurant_name')
    location = request.form.get('location')
    notes = request.form.get('notes')
    
    photo = request.files.get('photo')
    photo_url = None

    if photo:
        filename = secure_filename(photo.filename)
        photo_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        photo.save(photo_path)
        photo_url = url_for('uploaded_file', filename=filename, _external=True)


    review = Review(
        restaurant_name=restaurant_name,
        location=location,
        notes=notes,
        photo_url=photo_url,
        user_id=user_id,
    )
    
    db.session.add(review)
    db.session.commit()
    
    return jsonify({'message': 'Review added successfully'}), 201

@app.route('/edit-review/<int:review_id>', methods=['PUT'])
@jwt_required()
def edit_review(review_id):
    user_id = get_jwt_identity()
    curr_review = Review.query.get(review_id)

    if not curr_review or curr_review.user_id != user_id:
        return jsonify({'message': 'Review not found or access denied'}), 404
    
    updated_note = request.json.get('notes', curr_review.notes)
    if updated_note:
        curr_review.notes = updated_note
        db.session.commit()
        return jsonify({'message': 'Updated the selected review', 'updated_note': updated_note}), 200
    else:
        return jsonify({'message': 'Invalid input'}), 400

@app.route('/delete-review/<int:review_id>', methods=['DELETE'])
@jwt_required()
def delete_review(review_id):
    user_id = get_jwt_identity()
    curr_review = Review.query.get(review_id)

    if not curr_review or curr_review.user_id != user_id:
        return jsonify({'message': 'Review not found or access denied'}), 404
    
    db.session.delete(curr_review)
    db.session.commit()

    return jsonify({'message': 'Deleted the selected review'}), 200

YELP_API_KEY = 'ummCpIkI7Wn4Rz804XeaIxsBSSNei5KFxzTl3vor1oJ2hl592M_qpKiy_bNf5eeb-hscmukmIZHWPmefXjO1W32Y_wznEL7pdfyHT9FDTYzymj2MEsQBxgUKPkPmZ3Yx'
YELP_API_BASE = 'https://api.yelp.com/v3/businesses/search'

@app.route('/yelp-search')
def yelp_search():
    query = request.args.get('query')
    headers = {
        'Authorization': f'Bearer {YELP_API_KEY}'
    }
    params = {
        'term': query,
        'location': 'New York, NY',  # Or use user-provided location
        'limit': 10,
        'categories': 'restaurants'
    }

    res = requests.get(YELP_API_BASE, headers=headers, params=params)
    data = res.json()

    return jsonify(data.get('businesses', []))

@app.route('/me')
@jwt_required()
def me():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    return jsonify({ "email": user.email })


if __name__ == '__main__':
    app.run(debug=True)
