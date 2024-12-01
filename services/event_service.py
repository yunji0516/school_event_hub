from sqlalchemy.sql import func
from models import db, Event, Participant

def get_most_popular_event():
    result = db.session.query(
        Event.title,
        func.count(Participant.id).label("participant_count")
    ).join(Participant, Event.id == Participant.event_id)\
     .group_by(Event.id)\
     .order_by(func.count(Participant.id).desc())\
     .limit(1)\
     .first()
    
    return result