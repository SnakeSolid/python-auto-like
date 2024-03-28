from config import DATABASE_PATH, DATABASE_ROOT
from database import Database
from model import Model
from os.path import join, isfile
from photo import analyze_photo
import cv2
import numpy as np
import pickle

DATA_X_PATH = join(DATABASE_ROOT, "X.npy")
DATA_Y_PATH = join(DATABASE_ROOT, "y.npy")


def _create_dataset(photos, database):
    if isfile(DATA_X_PATH) and isfile(DATA_Y_PATH):
        X = np.load(DATA_X_PATH)
        y = np.load(DATA_Y_PATH)

        return (X, y)

    n_photos = len(photos)
    X = []
    y = []

    for (index, (photo_id, _, path, mark)) in enumerate(photos):
        if index % 10 == 0:
            print("Processed {}/{} ({:0.1f}%)".format(index, n_photos,
                                                      100 * index / n_photos))

        if not mark in ["like", "dislike"]:
            continue

        embedding = database.select_photo_embedding(photo_id)

        if embedding is None:
            (face, embedding) = analyze_photo(photo_id, path)

            if face is None:
                continue

            database.insert_photo_embedding(photo_id, pickle.dumps(embedding))
        else:
            embedding = pickle.loads(embedding)

        X.append(embedding)
        y.append(1.0 if mark == "like" else 0.0)

    X = np.array(X)
    y = np.array(y)

    np.save(DATA_X_PATH, X)
    np.save(DATA_Y_PATH, y)

    return (X, y)


if __name__ == "__main__":
    database = Database(DATABASE_PATH)
    photos = database.all_photos()
    X, y = _create_dataset(photos, database)
    model = Model()
    model.train(X, y)
    model.save()
