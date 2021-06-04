import os
from flask_login import current_user as cu
from hashlib import sha256

from app import session
from app.models import Festival, participants as prts

from config import Config


def get_festival_selection():
    result = [(-1, '')]
    festivals = session.query(Festival) \
        .join(prts, Festival.id == prts.c.festival_id) \
        .filter(prts.c.participant_id == cu.id).all()
    for f in festivals:
        result.append((f.id, f.title))
    return result


def get_images(f_id):
    base_path = Config.UPLOAD_PATH
    valid_extensions = Config.UPLOAD_EXTENSIONS
    path = os.path
    target_path = path.join(base_path, '{}/{}'.format(f_id, cu.id))

    images_dict = []
    dir_content = os.walk(target_path, topdown=False)
    path_separator = path.sep
    for root, directories, files in dir_content:
        for f in files:
            ext = path.splitext(f)[1]
            f_path = path.join(root, f)
            split = f_path.split(path_separator)
            if ext.lower() not in valid_extensions:
                continue
            html_path = '/{}/{}/{}/{}/{}'.format(split[-5], split[-4], split[-3], split[-2], split[-1])
            # using the hash as ID for each image preview
            path_hash = sha256(html_path.encode('utf-8')).hexdigest()
            images_dict.append({'filename': f, 'filepath': html_path, 'hash': path_hash})
    return images_dict
