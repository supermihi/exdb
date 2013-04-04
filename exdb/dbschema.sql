DROP TABLE IF EXISTS exercises;

CREATE TABLE exercises (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    creator STRING NOT NULL,
    number INTEGER NOT NULL,
    description TEXT,
    modified datetime NOT NULL,
    tex_exercise TEXT,
    tex_solution TEXT
);

DROP TABLE IF EXISTS preambles;
CREATE TABLE preambles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tex_preamble TEXT NOT NULL
);

DROP TABLE IF EXISTS ex_pre_rel;
CREATE TABLE ex_pre_rel (
    exercise INTEGER,
    preamble INTEGER,
    FOREIGN KEY(exercise) REFERENCES exercises(id),
    FOREIGN KEY(preamble) REFERENCES preambles(id)
);

DROP TABLE IF EXISTS tags;
CREATE TABLE tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tag STRING NOT NULL
);

DROP TABLE IF EXISTS ex_tags_rel;
CREATE TABLE ex_tags_rel (
    exercise INTEGER,
    tag INTEGER,
    FOREIGN KEY(exercise) REFERENCES exercises(id),
    FOREIGN KEY(tag) REFERENCES tags(id)
);
    