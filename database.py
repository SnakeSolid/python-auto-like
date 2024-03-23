from collections import namedtuple
from config import PHOTO_DIR, VIDEO_DIR, DATABASE_ROOT
from hashlib import sha3_256
from os import makedirs
from os.path import join
from threading import Lock
from uuid import uuid4
import collections
import mimetypes
import sqlite3
import urllib.request

INSERT_PROFILE = """
INSERT INTO profile (id, domain, name, age, description)
VALUES (?, ?, ?, ?, ?)
ON CONFLICT DO NOTHING
"""

INSERT_PHOTO = """
INSERT INTO photo (id, path, mark)
VALUES (?, ?, ?)
ON CONFLICT DO NOTHING
"""

INSERT_VIDEO = """
INSERT INTO video (id, path)
VALUES (?, ?)
ON CONFLICT DO NOTHING
"""

SET_PHOTO_PROFILE = """
UPDATE photo SET profile = ? WHERE id = ?
"""

SET_VIDEO_PROFILE = """
UPDATE video SET profile = ? WHERE id = ?
"""

SET_PROFILE_MARK = """
UPDATE photo SET mark = ? WHERE profile = ?
"""

SELECT_PHOTO = """
SELECT id, profile, path, mark FROM photo WHERE id = ?
"""

SELECT_PROFILE_PHOTOS = """
SELECT id, profile, path, mark FROM photo WHERE profile = ?
"""

SELECT_PHOTOS = """
SELECT id, profile, path, mark FROM photo
"""

SELECT_VIDEO = """
SELECT id, profile, path FROM video WHERE id = ?
"""


def path_for(base, part, hash, extension):
    directory = join(base, part, hash[0], hash[1])
    file_path = join(part, hash[0], hash[1], hash + extension)
    full_path = join(directory, hash + extension)

    makedirs(directory, exist_ok=True)

    return file_path, full_path


PhotoData = namedtuple("PhotoData", ["id", "profile", "path", "mark"])
VideoData = namedtuple("VideoData", ["id", "profile", "path"])


class Database:

    def __init__(self, path):
        init_script = open("initialize.sql", "r").read()

        self.connection = sqlite3.connect(path, check_same_thread=False)
        self.connection.executescript(init_script)
        self.connection.commit()

    def all_photos(self):
        return [
            PhotoData(row[0], row[1], row[2], row[3])
            for row in self.connection.execute(SELECT_PHOTOS).fetchall()
        ]

    def save_profile(self, profile):
        photo_ids = []
        video_ids = []

        for photo in profile.photos:
            try:
                photo_id = self.save_photo(photo)
                photo_ids.append(photo_id)
            except:
                print('Failed to save photo `{}`'.format(photo))

        for video in profile.videos:
            try:
                video_id = self.save_video(video)
                video_ids.append(video_id)
            except:
                print('Failed to save video `{}`'.format(video))

        profile_id = self._find_profile(photo_ids, video_ids)

        if profile_id == None:
            profile_id = str(uuid4())

        self.connection.execute(INSERT_PROFILE,
                                (profile_id, profile.domain, profile.name,
                                 profile.age, profile.description))
        self._set_profile(profile_id, photo_ids, video_ids)
        self.connection.commit()

        return profile_id

    def set_like(self, profile_id):
        self.connection.execute(SET_PROFILE_MARK, ("like", profile_id))
        self.connection.commit()

    def set_dislike(self, profile_id):
        self.connection.execute(SET_PROFILE_MARK, ("dislike", profile_id))
        self.connection.commit()

    def _set_profile(self, profile_id, photo_ids, video_ids):
        ids = set()

        for photo_id in photo_ids:
            self.connection.execute(SET_PHOTO_PROFILE, (profile_id, photo_id))

        for video_id in video_ids:
            self.connection.execute(SET_VIDEO_PROFILE, (profile_id, video_id))

    def _find_profile(self, photo_ids, video_ids):
        ids = set()

        for photo_id in photo_ids:
            data = self.select_photo(photo_id)

            if data is not None and data.profile is not None:
                ids.add(data.profile)

        for video_id in video_ids:
            data = self.select_video(video_id)

            if data is not None and data.profile is not None:
                ids.add(data.profile)

        if len(ids) == 1:
            return sorted(ids)[0]
        else:
            return None

    def select_profile_photos(self, profile_id):
        result = []

        for row in self.connection.execute(SELECT_PROFILE_PHOTOS,
                                           (profile_id, )).fetchall():
            result.append(PhotoData(row[0], row[1], row[2], row[3]))

        return result

    def select_photo(self, photo_id):
        row = self.connection.execute(SELECT_PHOTO, (photo_id, )).fetchone()

        if row is not None:
            return PhotoData(row[0], row[1], row[2], row[3])
        else:
            return None

    def select_video(self, video_id):
        row = self.connection.execute(SELECT_VIDEO, (video_id, )).fetchone()

        if row is not None:
            return VideoData(row[0], row[1], row[2])
        else:
            return None

    def set_photo_profile(self, photo_id, profile_id):
        self.connection.execute(SET_PHOTO_PROFILE, (photo_id, profile_id))
        self.connection.commit()

    def set_video_profile(self, video_id, profile_id):
        self.connection.execute(SET_VIDEO_PROFILE, (video_id, profile_id))
        self.connection.commit()

    def save_photo(self, photo):
        response = urllib.request.urlopen(photo)
        data = response.read()
        content_type = response.headers['content-type']
        extension = mimetypes.guess_extension(content_type)
        photo_id = sha3_256(data).hexdigest()
        (file_path, full_path) = path_for(DATABASE_ROOT, PHOTO_DIR, photo_id,
                                          extension)

        with open(full_path, "wb") as handle:
            handle.write(data)

        self.connection.execute(INSERT_PHOTO, (photo_id, file_path, "none"))
        self.connection.commit()

        return photo_id

    def save_video(self, video):
        response = urllib.request.urlopen(video)
        data = response.read()
        content_type = response.headers['content-type']
        extension = mimetypes.guess_extension(content_type)
        video_id = sha3_256(data).hexdigest()
        (file_path, full_path) = path_for(DATABASE_ROOT, VIDEO_DIR, video_id,
                                          extension)

        with open(full_path, "wb") as handle:
            handle.write(data)

        self.connection.execute(INSERT_VIDEO, (video_id, file_path))
        self.connection.commit()

        return photo_id


class Profile:

    def __init__(self, domain, name, age, description, photos=[], videos=[]):
        self.domain = domain
        self.name = name
        self.age = age
        self.description = description
        self.photos = sorted(photos)
        self.videos = sorted(videos)
