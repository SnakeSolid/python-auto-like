CREATE TABLE IF NOT EXISTS profile (
    id TEXT NOT NULL,
    domain TEXT NOT NULL,
    name TEXT NOT NULL,
    age INTEGER,
    description TEXT NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS profile_id ON profile (id);

CREATE TABLE IF NOT EXISTS photo (
    id TEXT NOT NULL,
    profile TEXT,
    path TEXT NOT NULL,
    mark TEXT NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS photo_id ON photo (id);
CREATE UNIQUE INDEX IF NOT EXISTS photo_profile_id ON photo (profile, id);

CREATE TABLE IF NOT EXISTS video (
    id TEXT NOT NULL,
    profile TEXT,
    path TEXT NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS video_id ON video (id);
CREATE UNIQUE INDEX IF NOT EXISTS video_profile_id ON video (profile, id);
