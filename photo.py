from collections import namedtuple
from config import DATABASE_ROOT
from deepface import DeepFace
from os.path import join
import cv2
import numpy as np

BACKEND = "yunet"
MODEL = "Facenet512"
ACTIONS = ["age", "gender", "race"]

Face = namedtuple("Face", ["index", "age", "confidence", "gender", "race"])


def analyze_photo(image):
    image_height, image_width = image.shape[0], image.shape[1]
    faces = DeepFace.analyze(img_path=image,
                             enforce_detection=False,
                             actions=ACTIONS,
                             detector_backend=BACKEND,
                             silent=True)
    n_faces = len(faces)

    # If face not found, return None
    if n_faces == 0 or (n_faces == 1 and faces[0]["face_confidence"] == 0):
        return None

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

    return Face(face_index, face["age"], face["face_confidence"],
                face["dominant_gender"], face["dominant_race"])


def represent_photo(image, face):
    faces = DeepFace.represent(img_path=image,
                               enforce_detection=False,
                               model_name=MODEL,
                               detector_backend=BACKEND)
    index = face.index

    if len(faces) <= index:
        return None

    embedding = faces[index]["embedding"]

    return np.array(embedding)


def _from_logit(logit):
    return np.exp(logit) / (1 + np.exp(logit))


def analyze_photos(model, photos):
    X = []

    for (index, (_, _, path, _)) in enumerate(photos):
        image_path = join(DATABASE_ROOT, path)
        image = cv2.imread(image_path)

        if image is None:
            continue

        face = analyze_photo(image)

        if face is None:
            continue

        embedding = represent_photo(image, face)

        if embedding is None:
            continue

        X.append(embedding)

    if len(X) == 0:
        return 0.0

    X = np.array(X)
    y = model.predict(X)

    return _from_logit(np.sum(y))
