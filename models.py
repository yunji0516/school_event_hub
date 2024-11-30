from flask_sqlalchemy import SQLAlchemy
import re

db = SQLAlchemy()

# User 테이블
class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password = db.Column(db.String(255), nullable=False)
    events = db.relationship('Event', backref='user', lazy=True)  # 관계 설정

# Location 테이블 (정규화된 테이블)
class Location(db.Model):
    __tablename__ = 'location'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    events = db.relationship('Event', backref='location', lazy=True)

# Event 테이블
class Event(db.Model):
    __tablename__ = 'event'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False, index=True)  # 제목 인덱스 추가
    date = db.Column(db.Date, nullable=False, index=True)  # 날짜 인덱스 추가
    location_id = db.Column(db.Integer, db.ForeignKey('location.id', ondelete='SET NULL'))
    description = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False, index=True)  # 외래키 인덱스 추가
    participants = db.relationship('Participant', backref='event', lazy=True, cascade="all, delete-orphan")
    feedbacks = db.relationship('Feedback', backref='event', lazy=True, cascade="all, delete-orphan")

    __table_args__ = (
        db.CheckConstraint("title <> ''", name="check_title_not_empty"),
        db.CheckConstraint("date >= '2024-12-01'", name="check_event_future_date"),
    )

# Participant 테이블
class Participant(db.Model):
    __tablename__ = 'participant'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    contact = db.Column(db.String(15), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id', ondelete='CASCADE'), nullable=False, index=True)
    attendance = db.Column(db.Boolean, default=False)
    uuid = db.Column(db.String(36), unique=True, nullable=False)

    # contact 유효성 검사
    @staticmethod
    def validate_contact(contact):
        pattern = r'^\+?\d{10,15}$'
        if not re.match(pattern, contact):
            raise ValueError("Invalid contact format. It must be a phone number with 10-15 digits.")

    def __init__(self, **kwargs):
        contact = kwargs.get('contact')
        if contact:
            self.validate_contact(contact)
        super().__init__(**kwargs)

# Feedback 테이블
class Feedback(db.Model):
    __tablename__ = 'feedback'
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id', ondelete='CASCADE'), nullable=False, index=True)
    feedback_text = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer, nullable=False)

    __table_args__ = (
        db.CheckConstraint("feedback_text <> ''", name='check_feedback_not_empty'),
        db.CheckConstraint('rating >= 1 AND rating <= 5', name='check_rating_range'),
    )
