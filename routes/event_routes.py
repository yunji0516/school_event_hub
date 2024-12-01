from flask import Blueprint, jsonify, render_template, session, request, redirect, url_for, flash
from models import db, User, Event, Participant, Feedback, Location
import uuid
from services.event_service import get_most_popular_event

# 이벤트 블루프린트 정의
event_bp = Blueprint('event_bp', __name__, url_prefix='/events')

# 이벤트 조회
@event_bp.route('/')
def list_events():
    search_query = request.args.get('search', '')  # 검색어 가져오기 (기본값: 빈 문자열)
    
    if search_query:
        # 제목 또는 설명에 검색어가 포함된 이벤트를 필터링 (대소문자 구분 없음)
        events = Event.query.filter(
            Event.title.ilike(f"%{search_query}%") | Event.description.ilike(f"%{search_query}%")
        ).all()
    else:
        # 검색어가 없으면 모든 이벤트 반환
        events = Event.query.order_by(Event.date.desc()).all()
    
    return render_template('events.html', events=events, search_query=search_query)

# 새로운 이벤트 등록
@event_bp.route('/create', methods=['GET', 'POST'])
def create_event():
    if 'user_id' not in session:
        flash('로그인이 필요합니다.', 'error')
        return redirect(url_for('auth_bp.login'))
    
    # 권한 확인
    user = User.query.get(session['user_id'])
    if not user.is_admin() and not user.is_superadmin():
        flash('이벤트 생성 권한이 없습니다. 관리자 권한을 요청하세요.', 'error')
        return redirect(url_for('event_bp.list_events'))

    if request.method == 'POST':
        title = request.form.get('title')
        date = request.form.get('date')
        location_name = request.form.get('location')
        description = request.form.get('description')

        # 필수 필드 확인
        if not title or not date or not location_name:
            flash('모든 필드를 입력해야 합니다.', 'error')
            return render_template('create_event.html')

        # 위치 저장 또는 기존 위치 확인
        location = Location.query.filter_by(name=location_name).first()
        if not location:
            location = Location(name=location_name)
            db.session.add(location)
            db.session.commit()

        # 이벤트 생성
        event = Event(
            title=title,
            date=date,
            location_id=location.id,
            description=description,
            user_id=user.id
        )
        try:
            db.session.add(event)
            db.session.commit()
            flash('이벤트가 성공적으로 생성되었습니다.', 'success')
            return redirect(url_for('event_bp.list_events'))
        except Exception as e:
            db.session.rollback()
            flash(f'이벤트 생성 중 오류가 발생했습니다: {str(e)}', 'error')

    return render_template('create_event.html')

# 이벤트 삭제
@event_bp.route('/delete/<int:id>', methods=['POST'])
def delete_event(id):
    event = Event.query.get_or_404(id)
    try:
        db.session.delete(event)
        db.session.commit()
        flash('이벤트가 성공적으로 삭제되었습니다.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'이벤트 삭제 중 오류가 발생했습니다: {str(e)}', 'error')
    return redirect(url_for('event_bp.list_events'))


@event_bp.route('/<int:event_id>')
def event_detail(event_id):
    event = Event.query.get_or_404(event_id)  # ID로 이벤트 검색
    return render_template('event_detail.html', event=event)

# 참가자 등록
@event_bp.route('/<int:event_id>/register_participant', methods=['GET', 'POST'])
def register_participant(event_id):
    # 이벤트가 존재하는지 확인
    event = Event.query.get_or_404(event_id)

    # 로그인 확인
    if 'user_id' not in session:
        flash('참가 신청을 하려면 로그인이 필요합니다.', 'error')
        return redirect(url_for('auth_bp.login'))

    if request.method == 'POST':
        # 폼 데이터 가져오기
        name = request.form.get('name')
        contact = request.form.get('contact')
        student_id = request.form.get('student_id')
        participant_uuid = str(uuid.uuid4())

        # 필드 검증
        if not name or not contact or not student_id:
            flash('이름과 연락처를 모두 입력해야 합니다.', 'error')
            return render_template('event_detail.html', event=event)

        # 학번 중복 확인
        if Participant.query.filter_by(event_id=event_id, student_id=student_id).first():
            flash('이미 해당 학번으로 등록된 참가자가 있습니다.', 'error')
            return render_template('register_participant.html', event=event)

        try:
            # 연락처 유효성 검사
            Participant.validate_contact(contact)

            # 참가자 생성
            participant = Participant(
                name=name,
                contact=contact,
                student_id=student_id,
                event_id=event_id,
                uuid=participant_uuid,
                attendance=True,
                user_id=session['user_id']  # 현재 로그인한 사용자의 ID를 할당
            )
            db.session.add(participant)
            db.session.commit()

            flash('참가 신청이 성공적으로 완료되었습니다!', 'success')
            participant_link = url_for('event_bp.participant_details', event_id=event_id, uuid=participant_uuid, _external=True)
            return render_template('register_success.html', participant_link=participant_link)

        except ValueError as ve:
            flash(f'유효하지 않은 연락처 형식입니다: {ve}', 'error')
        except Exception as e:
            db.session.rollback()
            flash(f'참가자 등록 중 오류가 발생했습니다: {str(e)}', 'error')

        return render_template('event_detail.html', event=event)

    # GET 요청에 대한 처리
    return render_template('event_detail.html', event=event)

# 이벤트 업데이트
@event_bp.route('/update/<int:id>', methods=['GET', 'POST'])
def update_event(id):
    event = Event.query.get_or_404(id)

    if request.method == 'POST':
        event.title = request.form.get('title')
        event.date = request.form.get('date')
        event_location = request.form.get('location')
        event.description = request.form.get('description')

        # Location 업데이트
        if event_location:
            location = Location.query.filter_by(name=event_location).first()
            if not location:
                location = Location(name=event_location)
                db.session.add(location)
            event.location = location

        try:
            db.session.commit()
            flash('이벤트가 성공적으로 수정되었습니다.', 'success')
            return redirect(url_for('auth_bp.mypage'))
        except Exception as e:
            db.session.rollback()
            flash(f'이벤트 수정 중 오류가 발생했습니다: {str(e)}', 'error')
            return redirect(url_for('event_bp.update_event', id=id))

    return render_template('update_event.html', event=event)

# 행사별 참석률 통계
@event_bp.route('/stats/<int:event_id>')
def event_stats(event_id):
    event = Event.query.get_or_404(event_id)
    total_participants = Participant.query.filter_by(event_id=event_id).count()
    attended_participants = Participant.query.filter_by(event_id=event_id, attendance=True).count()
    attendance_rate = (attended_participants / total_participants) * 100 if total_participants > 0 else 0
    return render_template('event_stats.html', event=event, attendance_rate=attendance_rate)


@event_bp.route('/<int:event_id>/participants', methods=['GET'])
def participant_list(event_id):
    # 이벤트 가져오기
    event = Event.query.get_or_404(event_id)

    # 참가자 목록 가져오기
    participants = Participant.query.filter_by(event_id=event_id).all()

    # 총 참가자 수 계산
    total_participants = len(participants)

    # 참석자 수 계산
    attendees = sum(1 for p in participants if p.attendance)
    attendance_rate = (attendees / total_participants * 100) if total_participants > 0 else 0

    # 피드백 가져오기
    feedbacks = Feedback.query.filter_by(event_id=event_id).all()

    return render_template(
        'participant_list.html',
        event=event,
        participants=participants,
        total_participants=total_participants,
        attendance_rate=attendance_rate,
        feedbacks=feedbacks
    )

# 참가자 정보 조회 및 수정
@event_bp.route('/<int:event_id>/participants/<uuid>', methods=['GET', 'POST'])
def participant_details(event_id, uuid):
    # 해당 참가자 정보 가져오기
    participant = Participant.query.filter_by(uuid=uuid, event_id=event_id).first_or_404()
    event = Event.query.get_or_404(event_id)

    if request.method == 'POST':
        # 폼에서 수정된 값 가져오기
        name = request.form.get('name')
        contact = request.form.get('contact')
        student_id = request.form.get('student_id')
        attendance = request.form.get('attendance') == 'True'  # 문자열을 Boolean으로 변환

        # 필수 필드 확인
        if not name or not contact or not student_id:
            flash('모든 필수 필드를 입력해야 합니다.', 'error')
            return render_template(
                'participant_details.html',
                participant=participant,
                feedbacks=Feedback.query.filter_by(event_id=event_id).all(),
                event=event
            )

        # 학번 중복 확인
        existing_participant = Participant.query.filter_by(event_id=event_id, student_id=student_id).first()
        if existing_participant and existing_participant.id != participant.id:
            flash('해당 학번은 이미 등록되어 있습니다.', 'error')
            return render_template(
                'participant_details.html',
                participant=participant,
                feedbacks=Feedback.query.filter_by(event_id=event_id).all(),
                event=event
            )

        try:
            # 데이터베이스에 변경 내용 저장
            participant.name = name
            participant.contact = contact
            participant.student_id = student_id
            participant.attendance = attendance
            db.session.commit()
            flash('참가자 정보가 성공적으로 수정되었습니다.', 'success')
            return redirect(url_for('auth_bp.mypage'))
        except Exception as e:
            db.session.rollback()
            flash(f'참가자 정보 수정 중 오류가 발생했습니다: {str(e)}', 'error')
            return render_template(
                'participant_details.html',
                participant=participant,
                feedbacks=Feedback.query.filter_by(event_id=event_id).all(),
                event=event
            )

    # 피드백 가져오기
    feedbacks = Feedback.query.filter_by(event_id=event_id).all()

    return render_template(
        'participant_details.html',
        participant=participant,
        feedbacks=feedbacks,
        event=event
    )



# 피드백 작성 라우트
@event_bp.route('/<int:event_id>/leave_feedback', methods=['POST'])
def leave_feedback(event_id):
    event = Event.query.get_or_404(event_id)

    feedback_text = request.form.get('feedback_text')
    rating = request.form.get('rating')

    if not feedback_text or not rating:
        flash('피드백 내용과 평점을 입력해주세요.', 'error')
        return redirect(url_for('event_bp.event_detail', event_id=event_id))

    try:
        feedback = Feedback(
            event_id=event_id,
            feedback_text=feedback_text,
            rating=int(rating)
        )
        db.session.add(feedback)
        db.session.commit()
        flash('피드백이 성공적으로 제출되었습니다.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'피드백 제출 중 오류가 발생했습니다: {str(e)}', 'error')

    return redirect(url_for('auth_bp.mypage', event_id=event_id))

@event_bp.route('/<int:event_id>/delete_feedback/<int:feedback_id>', methods=['POST'])
def delete_feedback(event_id, feedback_id):
    feedback = Feedback.query.get_or_404(feedback_id)
    try:
        db.session.delete(feedback)
        db.session.commit()
        flash('피드백이 성공적으로 삭제되었습니다.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'피드백 삭제 중 오류가 발생했습니다: {str(e)}', 'error')

    return redirect(url_for('auth_bp.mypage'))


@event_bp.route('/most_popular_event', methods=['GET'])
def most_popular_event():
    result = get_most_popular_event()
    if result:
        return jsonify({
            "event_title": result.title,
            "participant_count": result.participant_count
        })
    return jsonify({"message": "No data found"})