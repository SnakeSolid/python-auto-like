from os.path import join

DATABASE_ROOT = "database/"
DATABASE_PATH = join(DATABASE_ROOT, "database.sqlite")
PHOTO_DIR = "photos"
VIDEO_DIR = "videos"
PHOTO_ROOT = join(DATABASE_ROOT, PHOTO_DIR)
VIDEO_ROOT = join(DATABASE_ROOT, VIDEO_DIR)
MODEL_PATH = join(DATABASE_ROOT, "model", "checkpoint")
