from flask_login import current_user as cu
from app import db
from app.models import Festival, participants as prts


def get_festival_selection():
    result = [(-1, '')]
    festivals = db.session.query(Festival) \
        .join(prts, Festival.id == prts.c.festival_id) \
        .filter(prts.c.participant_id == cu.id).all()
    for f in festivals:
        result.append((f.id, f.title))
    return result


def sub_directory_name(f_id, u_id):
    return '{}_{}'.format(f_id, u_id)
