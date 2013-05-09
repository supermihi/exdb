DROP TABLE IF EXISTS exercises;

CREATE TABLE exercises (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    creator TEXT NOT NULL,
    number INTEGER NOT NULL,
    description TEXT,
    modified datetime NOT NULL,
    tex_exercise TEXT,
    tex_solution TEXT
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
    type TEXT,
    parent INTEGER,
    mat_path TEXT,
    FOREIGN KEY(parent) REFERENCES tags(id)
);

DROP TABLE IF EXISTS exercises_tags;
CREATE TABLE exercises_tags (
    exercise INTEGER,
    tag TEXT,
    FOREIGN KEY(exercise) REFERENCES exercises(id) ON DELETE CASCADE
);