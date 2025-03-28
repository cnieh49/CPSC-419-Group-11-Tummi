from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from models import db, User
from werkzeug.utils import secure_filename
import os

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
    #user = User.query.get(user_id)
    #return render_template('dashboard.html', user=user)
    reviews = Review.query.filter_by(user_id=user_id).all()
    return render_template('dashboard.html', reviews=reviews)

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
        photo_url = photo_path

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

if __name__ == '__main__':
    app.run(debug=True)
