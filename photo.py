from collections import namedtuple
from config import DATABASE_ROOT
from deepface import DeepFace
from os.path import join
import cv2
import numpy as np
import pickle

BACKEND = "mtcnn"
MODEL = "Facenet512"
ACTIONS = ["age", "gender", "race"]

Face = namedtuple("Face", ["index", "age", "confidence", "gender", "race"])
AnalyzeResult = namedtuple("AnalyzeResult",
                           ["probability", "age", "gender", "race"])


def analyze_photo(image_id, path):
    image_path = join(DATABASE_ROOT, path)
    image = cv2.imread(image_path)

    if image is None:
        return (None, None)

    image_height, image_width = image.shape[0], image.shape[1]
    faces = DeepFace.analyze(img_path=image,
                             enforce_detection=False,
                             actions=ACTIONS,
                             detector_backend=BACKEND,
                             silent=True)
    face = [face for face in faces if face["face_confidence"] > 0]
    n_faces = len(faces)

    if n_faces == 0:
        return (None, None)

    face_index = 0
    face_delta = image_height**2 + image_width**2

    for (index, face) in enumerate(faces):
        region = face["region"]
        center_x, center_y = region["x"] + region["w"] / 2, region[
            "y"] + region["h"] / 2
        delta = (center_x - image_height)**2 + (center_y - image_width)**2

        if delta < face_delta:
            face_index = index
            face_delta = delta

    face = faces[face_index]
    face = Face(face_index, face["age"], face["face_confidence"],
                face["dominant_gender"].lower(), face["dominant_race"])
    faces = DeepFace.represent(img_path=image,
                               enforce_detection=False,
                               model_name=MODEL,
                               detector_backend=BACKEND)

    if len(faces) <= face_index:
        return (None, None)

    embedding = faces[face_index]["embedding"]

    return (face, np.array(embedding))


def analyze_photos(model, photos, database):
    X = []
    ages = []
    genders = []
    races = []

    for (index, (photo_id, _, path, _)) in enumerate(photos):
        embedding = database.select_photo_embedding(photo_id)

        if embedding is None:
            (face, embedding) = analyze_photo(photo_id, path)

            if face is None:
                continue

            ages.append(face.age)
            genders.append(face.gender)
            races.append(face.race)
            database.insert_photo_embedding(photo_id, pickle.dumps(embedding))
        else:
            embedding = pickle.loads(embedding)

        X.append(embedding)

    if len(X) == 0:
        return 0.0

    X = np.array(X)
    y = model.predict(X)
    m = np.median(y)

    if len(ages) > 0 and len(genders) > 0 and len(races) > 0:
        age = sorted(ages)[len(ages) // 2]
        gender = sorted(genders)[len(genders) // 2]
        race = sorted(races)[len(races) // 2]
    else:
        age = None
        gender = None
        race = None

    return AnalyzeResult(float((np.exp(m) / (1 + np.exp(m)))), age, gender,
                         race)
