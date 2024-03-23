from config import DATABASE_PATH, DATABASE_ROOT
from database import Database
from model import Model
from os.path import join, isfile
from photo import analyze_photo, represent_photo
import cv2
import numpy as np

DATA_X_PATH = join(DATABASE_ROOT, "X.npy")
DATA_Y_PATH = join(DATABASE_ROOT, "y.npy")


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
    database = Database(DATABASE_PATH)
    photos = database.all_photos()
    X, y = _create_dataset(photos)
    model = Model()
    model.train(X, y)
    model.save()
