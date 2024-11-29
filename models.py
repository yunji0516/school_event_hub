from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# User 테이블
class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    events = db.relationship('Event', backref='user', lazy=True)  # 관계 설정

# Event 테이블
class Event(db.Model):
    __tablename__ = 'event'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    date = db.Column(db.Date, nullable=False)
    location = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    participants = db.relationship('Participant', backref='event', lazy=True, cascade="all, delete-orphan")  # 참가자 관계 추가
    feedbacks = db.relationship('Feedback', backref='event', lazy=True, cascade="all, delete-orphan")  # 피드백 관계 추가

# Participant 테이블
class Participant(db.Model):
    __tablename__ = 'participant'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    contact = db.Column(db.String(15), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id', ondelete='CASCADE'), nullable=False)
    attendance = db.Column(db.Boolean, default=False)
    uuid = db.Column(db.String(36), unique=True, nullable=False)

    __table_args__ = (
        db.CheckConstraint("contact ~ '^\\+?\\d{10,15}$'", name='check_contact_format'),
    )


# Feedback 테이블
class Feedback(db.Model):
    __tablename__ = 'feedback'
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=False)
    feedback_text = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer, nullable=False)

    __table_args__ = (
        db.CheckConstraint("feedback_text <> ''", name='check_feedback_not_empty'),
        db.CheckConstraint('rating >= 1 AND rating <= 5', name='check_rating_range'),
    )