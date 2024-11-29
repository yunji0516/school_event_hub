from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy import text

from routes.auth_routes import auth_bp
from routes.event_routes import event_bp
from models import db, User, Event, Participant, Feedback

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:1234@localhost:3147/eventmanagement'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 데이터베이스 초기화
db.init_app(app)
migrate = Migrate(app, db)

#블루프린트 등록
app.register_blueprint(auth_bp)
app.register_blueprint(event_bp)

try:
    with app.app_context():
        db.session.execute(text('SELECT 1'))
    print("Database connection successful!")
except Exception as e:
    print(f"Database connection failed: {e}")

with app.app_context():
    print(app.url_map)

# 애플리케이션 실행
if __name__ == '__main__':
    app.run(debug=True)