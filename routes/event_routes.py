from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import db, Event, Participant, Feedback
import uuid

# 이벤트 블루프린트 정의
event_bp = Blueprint('event_bp', __name__, url_prefix='/events')

# 모든 이벤트 조회
@event_bp.route('/')
def list_events():
    events = Event.query.all()
    return render_template('events.html', events=events)

# 새로운 이벤트 등록
@event_bp.route('/create', methods=['GET', 'POST'])
def create_event():
    if request.method == 'POST':
        title = request.form.get('title')
        date = request.form.get('date')
        location = request.form.get('location')
        description = request.form.get('description')
        user_id = request.form.get('user_id')

        if not title or not date or not location or not user_id:
            flash('모든 필수 필드를 입력해야 합니다.', 'error')
            return render_template('create_event.html')

        try:
            event = Event(title=title, date=date, location=location, description=description, user_id=user_id)
            db.session.add(event)
            db.session.commit()
            flash('이벤트가 성공적으로 생성되었습니다.', 'success')
            return redirect(url_for('event_bp.list_events'))
        except Exception as e:
            db.session.rollback()
            flash(f'이벤트 생성 중 오류가 발생했습니다: {str(e)}', 'error')
            return render_template('create_event.html')

    return render_template('create_event.html')

# 이벤트 수정
@event_bp.route('/update/<int:id>', methods=['GET', 'POST'])
def update_event(id):
    event = Event.query.get_or_404(id)
    if request.method == 'POST':
        event.title = request.form.get('title')
        event.date = request.form.get('date')
        event.location = request.form.get('location')
        event.description = request.form.get('description')

        if not event.title or not event.date or not event.location:
            flash('모든 필수 필드를 입력해야 합니다.', 'error')
            return render_template('update_event.html', event=event)

        try:
            db.session.commit()
            flash('이벤트가 성공적으로 수정되었습니다.', 'success')
            return redirect(url_for('event_bp.list_events'))
        except Exception as e:
            db.session.rollback()
            flash(f'이벤트 수정 중 오류가 발생했습니다: {str(e)}', 'error')
            return render_template('update_event.html', event=event)

    return render_template('update_event.html', event=event)

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

# 참가자 등록
@event_bp.route('/<int:event_id>/register_participant', methods=['GET', 'POST'])
def register_participant(event_id):
    event = Event.query.get_or_404(event_id)
    if request.method == 'POST':
        name = request.form.get('name')
        contact = request.form.get('contact')
        participant_uuid = str(uuid.uuid4())

        if not name or not contact:
            flash('모든 필수 필드를 입력해야 합니다.', 'error')
            return render_template('register_participant.html', event=event)

        try:
            participant = Participant(name=name, contact=contact, event_id=event_id, uuid=participant_uuid, attendance=False)
            db.session.add(participant)
            db.session.commit()
            flash('참가자가 성공적으로 등록되었습니다.', 'success')
            participant_link = url_for('event_bp.participant_details', event_id=event_id, uuid=participant_uuid, _external=True)
            return render_template('register_success.html', participant_link=participant_link)
        except Exception as e:
            db.session.rollback()
            flash(f'참가자 등록 중 오류가 발생했습니다: {str(e)}', 'error')
            return render_template('register_participant.html', event=event)

    return render_template('register_participant.html', event=event)

# 참석 여부 업데이트 (관리자용)
@event_bp.route('/update_attendance/<int:participant_id>', methods=['POST'])
def update_attendance(participant_id):
    participant = Participant.query.get_or_404(participant_id)
    participant.attendance = request.form.get('attendance') == 'True'
    try:
        db.session.commit()
        flash('참석 여부가 성공적으로 업데이트되었습니다.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'참석 여부 업데이트 중 오류가 발생했습니다: {str(e)}', 'error')
    return redirect(url_for('event_bp.list_events'))

# 행사별 참석률 통계
@event_bp.route('/stats/<int:event_id>')
def event_stats(event_id):
    event = Event.query.get_or_404(event_id)
    total_participants = Participant.query.filter_by(event_id=event_id).count()
    attended_participants = Participant.query.filter_by(event_id=event_id, attendance=True).count()
    attendance_rate = (attended_participants / total_participants) * 100 if total_participants > 0 else 0
    return render_template('event_stats.html', event=event, attendance_rate=attendance_rate)
# 피드백 추가
@event_bp.route('/feedback/<int:event_id>', methods=['GET', 'POST'])
def leave_feedback(event_id):
    event = Event.query.get_or_404(event_id)
    if request.method == 'POST':
        feedback_text = request.form.get('feedback_text')
        rating = request.form.get('rating')

        if not feedback_text or not rating:
            flash('모든 필수 필드를 입력해야 합니다.', 'error')
            return render_template('leave_feedback.html', event=event)

        try:
            feedback = Feedback(event_id=event_id, feedback_text=feedback_text, rating=rating)
            db.session.add(feedback)
            db.session.commit()
            flash('피드백이 성공적으로 제출되었습니다.', 'success')
            return redirect(url_for('event_bp.list_events'))
        except Exception as e:
            db.session.rollback()
            flash(f'피드백 제출 중 오류가 발생했습니다: {str(e)}', 'error')
            return render_template('leave_feedback.html', event=event)

    return render_template('leave_feedback.html', event=event)

# 참가자 정보 조회 및 수정
@event_bp.route('/<int:event_id>/participants/<uuid>', methods=['GET', 'POST'])
def participant_details(event_id, uuid):
    participant = Participant.query.filter_by(uuid=uuid, event_id=event_id).first_or_404()
    if request.method == 'POST':
        participant.name = request.form.get('name')
        participant.contact = request.form.get('contact')
        participant.attendance = request.form.get('attendance')

        if not participant.name or not participant.contact:
            flash('모든 필수 필드를 입력해야 합니다.', 'error')
            return render_template('participant_details.html', participant=participant)

        try:
            db.session.commit()
            flash('참가자 정보가 성공적으로 수정되었습니다.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'참가자 정보 수정 중 오류가 발생했습니다: {str(e)}', 'error')

    return render_template('participant_details.html', participant=participant)