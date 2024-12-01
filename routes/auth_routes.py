from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Event, UserRole, Participant

auth_bp = Blueprint('auth_bp', __name__, url_prefix='/auth')

# 회원가입
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')

        # 이메일 중복 체크
        if User.query.filter_by(email=email).first():
            flash('이미 존재하는 이메일입니다.', 'error')
            return render_template('register.html')

        # 사용자 생성 및 저장
        hashed_password = generate_password_hash(password)
        user = User(name=name, email=email, password=hashed_password)
        try:
            db.session.add(user)
            db.session.commit()
            flash('회원가입이 성공적으로 완료되었습니다.', 'success')
            return redirect(url_for('home'))  # 홈으로 이동
        except Exception as e:
            db.session.rollback()
            flash(f'회원가입 중 오류가 발생했습니다: {str(e)}', 'error')

    return render_template('register.html')

# 로그인
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            # 세션 초기화
            session.clear()
            session['user_id'] = user.id
            session['user_name'] = user.name
            flash('로그인에 성공했습니다.', 'success')
            return redirect(url_for('home'))  # 홈으로 이동
        else:
            flash('이메일 또는 비밀번호가 올바르지 않습니다.', 'error')

    return render_template('login.html')

# 로그아웃
@auth_bp.route('/logout')
def logout():
    # 세션 초기화
    session.clear()
    flash('성공적으로 로그아웃되었습니다.', 'success')
    return redirect(url_for('home'))

@auth_bp.route('/request_admin', methods=['POST'])
def request_admin():
    user = User.query.get(session['user_id'])
    if user.role != UserRole.USER:
        flash('이미 관리자 권한이 있습니다.', 'info')
        return redirect(url_for('auth_bp.mypage'))

    # 관리자 권한 요청 처리 로직
    flash('관리자 권한 요청이 접수되었습니다.', 'success')
    return redirect(url_for('auth_bp.mypage'))


# 마이페이지
@auth_bp.route('/mypage')
def mypage():
    if 'user_id' not in session:
        flash('로그인이 필요합니다.', 'error')
        return redirect(url_for('auth_bp.login'))

    # 현재 로그인한 사용자 정보 가져오기
    user = User.query.get(session['user_id'])

    # 사용자가 생성한 행사
    created_events = Event.query.filter_by(user_id=user.id).all()

    # 사용자가 신청한 행사
    registered_events = db.session.query(
        Event.id.label('id'),
        Event.title.label('title'),
        Event.date.label('date'),
        Event.description.label('description'),
        Participant.attendance.label('attendance'),
        Participant.uuid.label('participant_uuid')
    ).join(Participant, Event.id == Participant.event_id)\
     .filter(Participant.user_id == user.id)\
     .all()

    # 관리자 권한 요청 목록 (superadmin 전용)
    admin_requests = None
    if user.is_superadmin():
        admin_requests = User.query.filter_by(role=UserRole.USER).all()

    return render_template(
        'mypage.html',
        user=user,
        events=created_events,
        registered_events=registered_events,
        admin_requests=admin_requests
    )

# 관리자 권한 요청 승인
@auth_bp.route('/approve_admin/<int:user_id>', methods=['POST'])
def approve_admin(user_id):
    if 'user_id' not in session:
        flash('로그인이 필요합니다.', 'error')
        return redirect(url_for('auth_bp.login'))

    # 현재 로그인한 사용자 확인
    current_user = User.query.get(session['user_id'])
    if not current_user.is_superadmin():
        flash('이 작업을 수행할 권한이 없습니다.', 'error')
        return redirect(url_for('auth_bp.mypage'))

    # 권한 요청 승인
    user = User.query.get_or_404(user_id)
    if user.role == UserRole.ADMIN:
        flash('해당 사용자는 이미 관리자입니다.', 'error')
        return redirect(url_for('auth_bp.mypage'))

    try:
        user.role = UserRole.ADMIN
        db.session.commit()
        flash(f'{user.name}님의 권한이 관리자(Admin)로 변경되었습니다.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'권한 변경 중 오류가 발생했습니다: {str(e)}', 'error')

    return redirect(url_for('auth_bp.mypage'))

# 관리자 권한 요청 삭제
@auth_bp.route('/delete_admin_request/<int:user_id>', methods=['POST'])
def delete_admin_request(user_id):
    if 'user_id' not in session:
        flash('로그인이 필요합니다.', 'error')
        return redirect(url_for('auth_bp.login'))

    # 현재 로그인한 사용자 확인
    current_user = User.query.get(session['user_id'])
    if not current_user.is_superadmin():
        flash('이 작업을 수행할 권한이 없습니다.', 'error')
        return redirect(url_for('auth_bp.mypage'))

    # 요청 삭제 (요청만 제거)
    user = User.query.get_or_404(user_id)
    if user.role != UserRole.USER:
        flash('해당 사용자는 이미 관리자 또는 슈퍼관리자입니다.', 'error')
        return redirect(url_for('auth_bp.mypage'))

    try:
        db.session.delete(user)
        db.session.commit()
        flash(f'{user.name}님의 권한 요청이 삭제되었습니다.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'요청 삭제 중 오류가 발생했습니다: {str(e)}', 'error')

    return redirect(url_for('auth_bp.mypage'))

@auth_bp.route('/delete_account', methods=['POST'])
def delete_account():
    if 'user_id' not in session:
        flash('로그인이 필요합니다.', 'error')
        return redirect(url_for('auth_bp.login'))

    try:
        user_id = session['user_id']
        # 현재 사용자를 가져옵니다.
        user = User.query.get(user_id)

        # 사용자가 생성한 모든 이벤트 삭제
        Event.query.filter_by(user_id=user_id).delete()

        # 사용자 삭제
        db.session.delete(user)
        db.session.commit()

        # 세션 초기화
        session.clear()

        flash('회원탈퇴가 완료되었습니다.', 'success')
        return redirect(url_for('home'))
    except Exception as e:
        db.session.rollback()
        flash(f'회원탈퇴 중 오류가 발생했습니다: {str(e)}', 'error')
        return redirect(url_for('auth_bp.mypage'))