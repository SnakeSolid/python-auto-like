from config import DATABASE_PATH, DATABASE_ROOT
from database import Database
from deepface import DeepFace
from keras import layers
from os.path import join
import cv2
import keras
import numpy as np
import tensorflow as tf

# serialized = np.array(embedding).tobytes().hex()
# embedding = np.frombuffer(bytes.fromhex(serialized))

BACKEND = "yunet"
MODEL = "Facenet512"
ACTIONS = [ "age", "gender", "race" ]


def process_photo(image):
    image_height, image_width = image.shape[0], image.shape[1]
    faces = DeepFace.analyze(img_path = image, enforce_detection = False, actions = ACTIONS, detector_backend = BACKEND, silent = True)
    n_faces = len(faces)

    # If face not found, return None
    if n_faces == 0 or (n_faces == 1 and faces[0]["face_confidence"] == 0):
        return None

    face_index = 0
    face_delta = image_height**2 + image_width**2

    for (index, face) in enumerate(faces):
        region = face["region"]
        center_x, center_y = region["x"] + region["w"] / 2, region["y"] + region["h"] / 2
        delta = (center_x - image_height)**2 + (center_y - image_width)**2

        if delta < face_delta:
            face_index = index
            face_delta = delta

    if n_faces > 1:
        print(faces[face_index])

    return faces[face_index]


if __name__ == "__main__":
    db = Database(DATABASE_PATH)
    photos = db.all_photos()


    for (index, (_, _, path, _)) in enumerate(photos):
        image_path = join(DATABASE_ROOT, path)
        image = cv2.imread(image_path)
        face = process_photo(image)

        if face is None:
            continue

        feaces = DeepFace.represent(img_path = image, enforce_detection = False, model_name = MODEL, detector_backend = BACKEND)

        if len(feaces) > 1:
            print(image_path)
            print(feaces)
            break

    #     for face in feaces:
    #         if face["face_confidence"] == 0:
    #             continue

    #         embedding = face["face_confidence"]
    #         serialized = np.array(embedding).tobytes().hex()

    # model = keras.Sequential()
    # model.add(layers.Dense(2, activation="relu"))
    # model.add(layers.Dense(3, activation="relu"))
    # model.add(layers.Dense(4))
