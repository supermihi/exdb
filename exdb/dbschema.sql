DROP TABLE IF EXISTS exercises;
CREATE TABLE exercises (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    creator TEXT NOT NULL,
    number INTEGER NOT NULL,
    description TEXT,
    modified DATETIME NOT NULL,
    tex_exercise TEXDICT,
    tex_solution TEXDICT
);

DROP TABLE IF EXISTS exercises_preambles;
CREATE TABLE exercises_preambles (
    exercise INTEGER,
    preamble TEXT,
    FOREIGN KEY(exercise) REFERENCES exercises(id) ON DELETE CASCADE
);

DROP TABLE IF EXISTS tags;
CREATE TABLE tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    is_tag BOOLEAN,
    mat_path TEXT
);

DROP TABLE IF EXISTS exercises_tags;
CREATE TABLE exercises_tags (
    exercise INTEGER,
    tag TEXT,
    FOREIGN KEY(exercise) REFERENCES exercises(id) ON DELETE CASCADE
);
