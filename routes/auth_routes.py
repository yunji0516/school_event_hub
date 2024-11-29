from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User

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
            return redirect(url_for('auth_bp.login'))
        except Exception as e:
            db.session.rollback()
            flash(f'회원가입 중 오류가 발생했습니다: {str(e)}', 'error')
            return render_template('register.html')

    return render_template('register.html')

# 로그인
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['user_name'] = user.name
            flash('로그인에 성공했습니다.', 'success')
            return redirect(url_for('event_bp.list_events'))
        else:
            flash('이메일 또는 비밀번호가 올바르지 않습니다.', 'error')

    return render_template('login.html')

# 로그아웃
@auth_bp.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('user_name', None)
    flash('성공적으로 로그아웃되었습니다.', 'success')
    return redirect(url_for('auth_bp.login'))
