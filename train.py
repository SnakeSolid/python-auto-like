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

# serialized = np.array(embedding).tobytes().hex()
# embedding = np.frombuffer(bytes.fromhex(serialized))

DATA_X_PATH = join(DATABASE_ROOT, "X.npy")
DATA_Y_PATH = join(DATABASE_ROOT, "y.npy")
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


def create_dataset():
    if isfile(DATA_X_PATH) and isfile(DATA_Y_PATH):
        X = np.load(DATA_X_PATH)
        y = np.load(DATA_Y_PATH)

        return (X, y)

    database = Database(DATABASE_PATH)
    photos = database.all_photos()
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

        face = analyze_photo(image)

        if face is None:
            continue

        embedding = represent_photo(image, face)
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


if __name__ == "__main__":
    X, y = create_dataset()
    model = keras.Sequential()
    model.add(layers.Dense(128, activation="relu"))
    model.add(layers.Dense(32, activation="relu"))
    model.add(layers.Dense(1))
    model.compile(
        optimizer=keras.optimizers.RMSprop(),
        loss=keras.losses.BinaryCrossentropy(),
        metrics=[keras.metrics.BinaryAccuracy()],
    )
    model.fit(X, y, batch_size=64, epochs=50, validation_data=(X, y))
    model.save_weights(MODEL_PATH)
    model.load_weights(MODEL_PATH)
