from deepface import DeepFace
from os.path import join
import sqlite3

connection = sqlite3.connect("database/database.sqlite")

for backend in [ "ssd", "mtcnn", "yunet" ]: # "opencv",
    for (path, ) in connection.execute("select path from photo"):
        image = join("database", path)

        try:
            faces = DeepFace.analyze(img_path=image,
                                     enforce_detection=False,
                                     actions=["age", "gender"],
                                     detector_backend=backend,
                                     silent=True)
        except ValueError:
            continue

        faces = [ face for face in faces if face["face_confidence"] > 0 ]
        faces = [ "{}={}".format(face["dominant_gender"], face["age"]) for face in faces ]

        print("{};{};{};{}".format(backend, path, len(faces), ",".join(faces)))
