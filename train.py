from collections import namedtuple
from config import DATABASE_PATH, MODEL_PATH, DATABASE_ROOT
from database import Database
from deepface import DeepFace
from keras import layers
from os.path import join, isfile
import cv2
import keras
import numpy as np
import tensorflow as tf
from model import Model

DATA_X_PATH = join(DATABASE_ROOT, "X.npy")
DATA_Y_PATH = join(DATABASE_ROOT, "y.npy")
BACKEND = "yunet"
MODEL = "Facenet512"
ACTIONS = ["age", "gender", "race"]

Face = namedtuple("Face", ["index", "age", "confidence", "gender", "race"])


def _analyze_photo(image):
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


def _represent_photo(image, face):
    faces = DeepFace.represent(img_path=image,
                               enforce_detection=False,
                               model_name=MODEL,
                               detector_backend=BACKEND)
    index = face.index

    if len(faces) <= index:
        return None

    embedding = faces[index]["embedding"]

    return np.array(embedding)


def _create_dataset(photos):
    if isfile(DATA_X_PATH) and isfile(DATA_Y_PATH):
        X = np.load(DATA_X_PATH)
        y = np.load(DATA_Y_PATH)

        return (X, y)

    n_photos = len(photos)
    X = []
    y = []

    for (index, (_, _, path, mark)) in enumerate(photos):
        if index % 10 == 0:
            print("Processed {}/{} ({:0.1f}%)".format(index, n_photos,
                                                      100 * index / n_photos))

        if not mark in ["like", "dislike"]:
            continue

        image_path = join(DATABASE_ROOT, path)
        image = cv2.imread(image_path)

        if image is None:
            continue

        face = _analyze_photo(image)

        if face is None:
            continue

        embedding = _represent_photo(image, face)
        label = 1 if mark == "like" else 0

        if embedding is None:
            continue

        X.append(embedding)
        y.append(label)

    X = np.array(X)
    y = np.array(y)

    np.save(DATA_X_PATH, X)
    np.save(DATA_Y_PATH, y)

    return (X, y)


def analyze_photos(model, photos):
    X = []

    for (index, (_, _, path, _)) in enumerate(photos):
        image_path = join(DATABASE_ROOT, path)
        image = cv2.imread(image_path)

        if image is None:
            continue

        face = _analyze_photo(image)

        if face is None:
            continue

        embedding = _represent_photo(image, face)

        if embedding is None:
            continue

        X.append(embedding)

    X = np.array(X)
    y = model.predict(X)
    logit = np.sum(y)

    print(np.exp(logit) / (1 + np.exp(logit)))


if __name__ == "__main__":
    database = Database(DATABASE_PATH)
    photos = database.all_photos()
    X, y = _create_dataset(photos)
    model = Model()
    model.train(X, y)
    model.save()
