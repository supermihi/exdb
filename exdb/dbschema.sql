CREATE TABLE IF NOT EXISTS exercises (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    creator TEXT NOT NULL,
    number INTEGER NOT NULL,
    description TEXT,
    modified DATETIME NOT NULL,
    tex_exercise TEXDICT,
    tex_solution TEXDICT
);
CREATE INDEX IF NOT EXISTS idxDesc ON exercises (description);

CREATE TABLE IF NOT EXISTS exercises_preambles (
    exercise INTEGER,
    preamble TEXT,
    FOREIGN KEY(exercise) REFERENCES exercises(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    is_tag BOOLEAN,
    mat_path TEXT
);
CREATE INDEX IF NOT EXISTS idxMatPath ON tags (mat_path);
CREATE INDEX IF NOT EXISTS idxIsTag ON tags (is_tag);

CREATE TABLE IF NOT EXISTS exercises_tags (
    exercise INTEGER,
    tag TEXT,
    FOREIGN KEY(exercise) REFERENCES exercises(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idxExTags ON exercises_tags (tag);