from app import app, db
from models import Event, Location, User, UserRole
from datetime import datetime
from werkzeug.security import generate_password_hash

# 데이터베이스 초기화 및 더미 데이터 추가
with app.app_context():
    db.create_all()

    # User 데이터 추가
    if not User.query.filter_by(id=1).first():
        default_user = User(
            id=1,
            name="김윤지",
            email="admin@example.com",
            password=generate_password_hash("admin123"),  # 비밀번호를 해시화
            role=UserRole.SUPERADMIN  # Enum을 사용할 경우 직접 Enum 값을 지정
        )
        db.session.add(default_user)
        db.session.commit()
        print("기본 사용자 추가됨.")


    # Location 데이터 추가
    if not Location.query.filter_by(name="체육관").first():
        loc1 = Location(name="체육관")
        db.session.add(loc1)
        print("체육관 데이터 추가됨.")
    
    if not Location.query.filter_by(name="음악실").first():
        loc2 = Location(name="음악실")
        db.session.add(loc2)
        print("음악실 데이터 추가됨.")
    
    db.session.commit()

    # 더미 이벤트 데이터 추가
    if not Event.query.filter_by(title="과학 전시회").first():
        event1 = Event(
            title="과학 전시회",
            description="학교에서 진행하는 과학 전시회입니다.",
            date=datetime(2024, 12, 15),
            location_id=Location.query.filter_by(name="체육관").first().id,
            user_id=1
        )
        db.session.add(event1)
        print("과학 전시회 이벤트 추가됨.")
    
    if not Event.query.filter_by(title="음악 콘서트").first():
        event2 = Event(
            title="음악 콘서트",
            description="학생들이 준비한 음악 공연.",
            date=datetime(2024, 12, 20),
            location_id=Location.query.filter_by(name="음악실").first().id,
            user_id=1
        )
        db.session.add(event2)
        print("음악 콘서트 이벤트 추가됨.")
    
    try:
        # 잘못된 날짜를 고쳐 추가하거나 테스트용으로 예외 처리
        invalid_event = Event(title="잘못된 행사", date=datetime(2024, 12, 1), user_id=1)  # 수정된 날짜
        db.session.add(invalid_event)
        db.session.commit()
        print("잘못된 행사 추가 완료.")  # 제약 조건을 만족할 경우
    except Exception as e:
        db.session.rollback()
        print(f"잘못된 데이터 추가 실패: {e}")

    print("더미 데이터 추가 완료!")
