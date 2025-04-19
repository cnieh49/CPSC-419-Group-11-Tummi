from flask import Flask, render_template, request, jsonify, redirect, url_for, send_from_directory, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, verify_jwt_in_request, set_access_cookies, unset_jwt_cookies
from flask_jwt_extended.exceptions import NoAuthorizationError
from models import db, User, Like
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import json
import requests
basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret'
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(basedir, 'db.sqlite')}"
app.config['JWT_SECRET_KEY'] = 'jwt-secret'
app.config['UPLOAD_FOLDER'] = './uploads'
app.config["JWT_TOKEN_LOCATION"] = ["cookies"]
app.config["JWT_COOKIE_SECURE"] = False
app.config["JWT_COOKIE_CSRF_PROTECT"] = False

db.init_app(app)
jwt = JWTManager(app)

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    restaurant_name = db.Column(db.String(120), nullable=False)
    location = db.Column(db.String(120), nullable=False)
    notes = db.Column(db.Text, nullable=True)
    photo_url = db.Column(db.String(255), nullable=True)
    pictures = db.Column(db.Text, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def get_pictures(self):
        return json.loads(self.pictures or "[]")

    def set_pictures(self, pictures_list):
        self.pictures = json.dumps(pictures_list)

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
    
    if user.first_name != "No name provided" and user.last_name != "No name provided":
        display_name = f"{user.first_name} {user.last_name}"
    elif user.first_name != "No name provided" and user.last_name == "No name provided":
        display_name = f"{user.first_name}"
    else:
        display_name = user.email
    
    return jsonify({
        "email": user.email,
        "display_name": display_name,
        "message": f"Welcome to Tummi, {display_name}!"
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
        'pictures': r.pictures,
        'timestamp': r.timestamp.strftime("%Y-%m-%d %H:%M:%S")
    } for r in reviews])

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/dashboard-page')
@jwt_required()
def dashboard_page():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    display_name = f"{user.first_name} {user.last_name}" if user.first_name and user.last_name else user.email

    return render_template(
        'dashboard.html',
        first_name=user.first_name,
        last_name=user.last_name,
        display_name=display_name,
        bio=user.bio,
        location=user.location,
        profile_picture=user.profile_picture
    )

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(email=data['email']).first()

    if user and user.check_password(data['password']):
        token = create_access_token(identity=str(user.id))
        resp = jsonify({'message': 'Login successful'})
        set_access_cookies(resp, token) 
        return resp, 200
        
    return jsonify({'message': 'Invalid credentials'}), 401

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'message': 'Email already exists'}), 409
    user = User(
        email=data['email'],
        first_name=data.get('first_name'), 
        last_name=data.get('last_name') 
    )
    user.set_password(data['password'])
    db.session.add(user)
    db.session.commit()
    return jsonify({'message': 'User registered successfully'}), 201

# @app.route('/profile-page')
# def profile_page():
#     return render_template('profile.html')

@app.route('/profile-page')
@jwt_required()
def profile_page():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    response = make_response(render_template(
        'profile.html',
        first_name=user.first_name or '',
        last_name=user.last_name or '',
        bio=user.bio or '',
        location=user.location or '',
        profile_picture=user.profile_picture or ''
    ))

    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    
    return response

@app.route('/edit-profile', methods=['POST'])
@jwt_required()
def edit_profile():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if 'profile_picture' in request.files:
        photo = request.files['profile_picture']
        if photo:
            filename = secure_filename(photo.filename)
            photo_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            photo.save(photo_path)
            user.profile_picture = url_for('uploaded_file', filename=filename, _external=True)
    
    user.first_name = request.form.get('first_name', user.first_name)
    user.last_name = request.form.get('last_name', user.last_name)
    user.bio = request.form.get('bio', user.bio)
    user.location = request.form.get('location', user.location)
    
    db.session.commit()
    return jsonify({'message': 'Profile updated successfully'}), 200

@app.route('/get-profile')
@jwt_required()
def get_profile():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    return jsonify({
        'first_name': user.first_name or '',
        'last_name': user.last_name or '',
        'bio': user.bio or '',
        'location': user.location or '',
        'profile_picture': user.profile_picture or ''
        #'profile_picture_url': user.profile_picture_url
    })

@app.route('/add-review', methods=['POST'])
@jwt_required()
def add_review():
    user_id = get_jwt_identity()
    restaurant_name = request.form.get('restaurant_name')
    location = request.form.get('location')
    notes = request.form.get('notes')
    
    pictures_files = request.files.getlist('pictures') 
    pictures_urls = []
    for picture in pictures_files:
        if picture:
            filename = secure_filename(picture.filename)
            picture_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            picture.save(picture_path)
            pictures_urls.append(url_for('uploaded_file', filename=filename, _external=True))

    review = Review(
        restaurant_name=restaurant_name,
        location=location,
        notes=notes,
        pictures=json.dumps(pictures_urls),  
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

    if not curr_review or curr_review.user_id != int(user_id):
        return jsonify({'message': 'Review not found or access denied'}), 404
    
    review_updated_bool = False
    updated_information = request.json

    if 'notes' in updated_information and updated_information['notes'] != curr_review.notes:
        curr_review.notes = updated_information['notes']
        review_updated_bool = True

    if 'pictures' in updated_information:
        if updated_information['pictures'] != curr_review.get_pictures():
            curr_review.set_pictures(updated_information['pictures'])
            review_updated_bool = True

    if review_updated_bool:
        db.session.commit()
        return jsonify({'message': 'Review updated successfully'}), 200
    else:
        return jsonify({'message': 'No changes detected'}), 200

@app.route('/delete-review/<int:review_id>', methods=['DELETE'])
@jwt_required()
def delete_review(review_id):
    user_id = get_jwt_identity()
    curr_review = Review.query.get(review_id)

    if not curr_review or curr_review.user_id != int(user_id):
        return jsonify({'message': 'Review not found or access denied'}), 404
    
    db.session.delete(curr_review)
    db.session.commit()

    return jsonify({'message': 'Deleted the selected review'}), 200

YELP_API_KEY = 'ummCpIkI7Wn4Rz804XeaIxsBSSNei5KFxzTl3vor1oJ2hl592M_qpKiy_bNf5eeb-hscmukmIZHWPmefXjO1W32Y_wznEL7pdfyHT9FDTYzymj2MEsQBxgUKPkPmZ3Yx'
YELP_API_BASE = 'https://api.yelp.com/v3/businesses/search'

CUISINE_TO_CATEGORY = {
    'Italian': 'italian',
    'Mexican': 'mexican',
    'Chinese': 'chinese',
    'Japanese': 'japanese',
    'Indian': 'indpak',
    'Thai': 'thai',
    'Korean': 'korean',
    'French': 'french',
    'American': 'newamerican',
    'Mediterranean': 'mediterranean',
    'Vietnamese': 'vietnamese'
}

@app.route('/yelp-search')
def yelp_search():
    query = request.args.get('query')
    price_filter = request.args.getlist('price')
    open_now_filter = request.args.get('open_now')
    cuisine_filter = request.args.getlist('categories')

    categories = []
    for cuisine in cuisine_filter:
        category = CUISINE_TO_CATEGORY.get(cuisine)
        if category:
            categories.append(category)

    headers = {
        'Authorization': f'Bearer {YELP_API_KEY}'
    }
    params = {
        'term': query,
        'location': 'New York, NY',  # Or use user-provided location
        'limit': 10,
        'categories': 'restaurants'
    }
    if price_filter:
        params['price'] = ','.join(price_filter)
    if open_now_filter == 'true':
        params['open_now'] = 'true'
    if categories:
        params['categories'] = ','.join(categories)

    res = requests.get(YELP_API_BASE, headers=headers, params=params)
    data = res.json()

    return jsonify(data.get('businesses', []))

@app.route('/me')
@jwt_required()
def me():
    user = User.query.get(get_jwt_identity())
    return jsonify({ "email": user.email, "id": user.id })

@app.route('/feed-page')
def feed_page():
    return render_template('feed.html')

@app.route('/feed')
@jwt_required()
def feed():
    user = User.query.get(get_jwt_identity())
    followed_ids = [u.id for u in user.followed.all()]

    reviews = Review.query.filter(Review.user_id.in_(followed_ids)).order_by(Review.timestamp.desc()).all()

    return jsonify([
        {
            'id': r.id,
            'restaurant_name': r.restaurant_name,
            'location': r.location,
            'notes': r.notes,
            'photo_url': r.photo_url,
            'pictures': r.pictures,
            'timestamp': r.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            'user_id': r.user_id,
            'email': r.user.email
        } for r in reviews
    ])

@app.route('/all-users')
@jwt_required()
def all_users():
    users = User.query.all()
    return jsonify([{'id': u.id, 'email': u.email} for u in users])

@app.route('/follow/<int:user_id>', methods=['POST'])
@jwt_required()
def follow_user(user_id):
    current_user = User.query.get(get_jwt_identity())
    target_user = User.query.get(user_id)

    if not target_user or current_user.id == user_id:
        return jsonify({'message': 'Invalid user'}), 400

    if not current_user.followed.filter_by(id=target_user.id).first():
        current_user.followed.append(target_user)
        db.session.commit()
        return jsonify({'message': f'Now following {target_user.email}'}), 200

    return jsonify({'message': 'Already following'}), 400

@app.route('/unfollow/<int:user_id>', methods=['POST'])
@jwt_required()
def unfollow_user(user_id):
    current_user = User.query.get(get_jwt_identity())
    target_user = User.query.get(user_id)

    if current_user.followed.filter_by(id=target_user.id).first():
        current_user.followed.remove(target_user)
        db.session.commit()
        return jsonify({'message': f'Unfollowed {target_user.email}'}), 200

    return jsonify({'message': 'Not following this user'}), 400

@app.route('/is-following/<int:user_id>')
@jwt_required()
def is_following(user_id):
    current_user = User.query.get(get_jwt_identity())
    user_friended = User.query.get(user_id)
    if not user_friended or current_user.id == user_id:
        return jsonify({'following': False})
    is_following = current_user.followed.filter_by(id=user_friended.id).first() is not None
    return jsonify({'following': is_following})

@app.route('/followers')
@jwt_required()
def get_followers():
    user = User.query.get(get_jwt_identity())
    return jsonify([{'id': u.id, 'email': u.email} for u in user.followers.all()])

@app.route('/following')
@jwt_required()
def get_following():
    user = User.query.get(get_jwt_identity())
    return jsonify([{'id': u.id, 'email': u.email} for u in user.followed.all()])

@app.route('/user/<int:user_id>')
def user_profile_page(user_id):
    user = User.query.get(user_id)
    if not user:
        return "User not found", 404
    
    display_name = f"{user.first_name} {user.last_name}" if user.first_name and user.last_name else user.email
    is_own_profile = (str(user.id) == str(user_id))
    
    return render_template(
        'indiv_profile.html',
        user_id=user.id,
        user_email=user.email,
        profile_picture=user.profile_picture,
        display_name=display_name,
        first_name=user.first_name,
        last_name=user.last_name,
        bio=user.bio,
        location=user.location,
        followers_count=len(user.followers.all()),
        following_count=len(user.followed.all())
    )
    
@app.route('/user-reviews/<int:user_id>')
@jwt_required()
def reviews_for_user(user_id):
    reviews = Review.query.filter_by(user_id=user_id).order_by(Review.timestamp.desc()).all()
    return jsonify([{
        'id': r.id,
        'restaurant_name': r.restaurant_name,
        'location': r.location,
        'notes': r.notes,
        'photo_url': r.photo_url,
        'pictures': r.get_pictures(),
        'timestamp': r.timestamp.strftime("%Y-%m-%d %H:%M:%S")
    } for r in reviews])
    
@app.route('/like/<int:review_id>', methods=['POST'])
@jwt_required()
def like_review(review_id):
    user_id = get_jwt_identity()
    existing = Like.query.filter_by(user_id=user_id, review_id=review_id).first()

    if existing:
        return jsonify({'message': 'Already liked'}), 400

    like = Like(user_id=user_id, review_id=review_id)
    db.session.add(like)
    db.session.commit()
    return jsonify({'message': 'Liked'}), 200

@app.route('/unlike/<int:review_id>', methods=['POST'])
@jwt_required()
def unlike_review(review_id):
    user_id = get_jwt_identity()
    like = Like.query.filter_by(user_id=user_id, review_id=review_id).first()

    if like:
        db.session.delete(like)
        db.session.commit()
        return jsonify({'message': 'Unliked'}), 200

    return jsonify({'message': 'Like not found'}), 404

@app.route('/likes-count/<int:review_id>')
@jwt_required()
def likes_count(review_id):
    count = Like.query.filter_by(review_id=review_id).count()
    user_id = get_jwt_identity()
    liked = Like.query.filter_by(user_id=user_id, review_id=review_id).first() is not None
    return jsonify({'count': count, 'liked_by_user': liked})

@app.route('/likes/<int:review_id>')
@jwt_required()
def get_likes(review_id):
    from models import Like, User  # just in case
    likes = Like.query.filter_by(review_id=review_id).all()
    users = [User.query.get(l.user_id) for l in likes]
    return jsonify([{'id': u.id, 'email': u.email} for u in users if u])

import json

@app.template_filter('parse_json')
def parse_json(value):
    try:
        return json.loads(value or "[]")
    except json.JSONDecodeError:
        return [] 
    
@app.route('/edit-review-images/<int:review_id>', methods=['POST'])
@jwt_required()
def edit_review_images(review_id):
    user_id = get_jwt_identity()
    review = Review.query.get(review_id)

    if not review or review.user_id != int(user_id):
        return jsonify({'message': 'Review not found or access denied'}), 404

    # Get current pictures from review
    current_pics = review.get_pictures()

    # Get list of URLs to remove from form
    to_remove = request.form.getlist('remove_pictures')
    updated_pics = [pic for pic in current_pics if pic not in to_remove]

    # Handle any new picture uploads
    new_pics = request.files.getlist('new_pictures')
    for pic in new_pics:
        if pic and pic.filename:
            filename = secure_filename(pic.filename)
            path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            pic.save(path)
            updated_pics.append(url_for('uploaded_file', filename=filename, _external=True))

    review.set_pictures(updated_pics)
    db.session.commit()

    return jsonify({'message': 'Images updated successfully', 'pictures': updated_pics}), 200

@app.route('/restaurant/<name>')
def restaurant_page(name):
    return render_template('restaurant.html')

@app.route('/restaurant-details/<name>')
@jwt_required()
def restaurant_details(name):
    try:
        response = requests.get(
            "https://api.yelp.com/v3/businesses/search",
            headers={"Authorization": f"Bearer {YELP_API_KEY}"},
            params={"term": name, "location": "New Haven"}
        )
        data = response.json()
        if data["businesses"]:
            return jsonify(data["businesses"][0])
        else:
            return jsonify({"error": "No details found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/restaurant-reviews/<restaurant_name>')
@jwt_required()
def restaurant_reviews(restaurant_name):
    user = User.query.get(get_jwt_identity())
    followed_ids = [u.id for u in user.followed.all()]
    
    reviews = Review.query.filter_by(restaurant_name=restaurant_name).filter(Review.user_id.in_(followed_ids)).order_by(Review.timestamp.desc()).all()

    return jsonify([{
        'id': r.id,
        'restaurant_name': r.restaurant_name,
        'location': r.location,
        'notes': r.notes,
        'pictures': r.pictures,
        'timestamp': r.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        'user_id': r.user_id,
        'email': r.user.email
    } for r in reviews])
    
@app.route('/explore')
def explore_page():
    return render_template('explore.html')

@app.route('/followers/<int:user_id>')
@jwt_required()
def get_followers_for_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404
    return jsonify([{'id': u.id, 'email': u.email} for u in user.followers.all()])


@app.route('/following/<int:user_id>')
@jwt_required()
def get_following_for_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': 'User not found'}), 404
    return jsonify([{'id': u.id, 'email': u.email} for u in user.followed.all()])

@jwt.unauthorized_loader
def custom_unauthorized_response(callback):
    return redirect(url_for('login_page', next=request.path, msg='login_required'))

@jwt.expired_token_loader
def custom_expired_token_callback(jwt_header, jwt_payload):
    return redirect(url_for('login_page', next=request.path, msg='login_required'))

if __name__ == '__main__':
    app.run(debug=True)
