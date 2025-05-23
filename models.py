"""
models.py

This module defines the database models for the application using SQLAlchemy. 
It includes models for users, reviews, likes, and a utility class for ranking reviews. 
The models are designed to handle relationships, such as followers and reviews, 
and provide utility methods for password hashing and verification.
"""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
# from sortedcontainers import SortedList

db = SQLAlchemy()

# Association table for followers
follows = db.Table('follows',
    db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('followed_id', db.Integer, db.ForeignKey('user.id'))
)

class User(db.Model):
    """
    Represents a user in the application.
    """
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    reviews = db.relationship('Review', backref='user', lazy=True)
    first_name = db.Column(db.String(120), nullable=True)
    last_name = db.Column(db.String(120), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    location = db.Column(db.String(120), nullable=True)
    profile_picture = db.Column(db.String(255), nullable=True)

    # Self-referential many-to-many
    followed = db.relationship(
        'User',
        secondary=follows,
        primaryjoin=(follows.c.follower_id == id),
        secondaryjoin=(follows.c.followed_id == id),
        backref=db.backref('followers', lazy='dynamic'),
        lazy='dynamic'
    )

    def set_password(self, password):
        """
        Hashes and sets the user's password.
        """
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """
        Verifies the user's password against the stored hash.
        """
        return check_password_hash(self.password_hash, password)

class Like(db.Model):
    """
    For a 'like' on a review by a user.
    """
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    review_id = db.Column(db.Integer, db.ForeignKey('review.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class ReviewEntry:
    """
    Wrapper for a review object, used for ranking comparisons.
    """
    def __init__(self, review):
        self.review = review  # SQLAlchemy Review object

    def __lt__(self, other):
        self_rank = self.review.ranking if self.review.ranking is not None else 5
        other_rank = other.review.ranking if other.review.ranking is not None else 5
        return self_rank > other_rank

    def __repr__(self):
        return f"<ReviewEntry {self.review.restaurant_name} (Rank: {self.review.ranking})>"
    