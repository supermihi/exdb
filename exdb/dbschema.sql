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
    FOREIGN KEY(exercise) REFERENCES exercises(id) ON DELETE CASCADE,
    FOREIGN KEY(preamble) REFERENCES preambles(id) ON DELETE CASCADE
);

DROP TABLE IF EXISTS tags;
CREATE TABLE tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tag STRING NOT NULL,
    category INTEGER,
    FOREIGN KEY(category) REFERENCES categories(id)
);

DROP TABLE IF EXISTS ex_tags_rel;
CREATE TABLE ex_tags_rel (
    exercise INTEGER,
    tag INTEGER,
    FOREIGN KEY(exercise) REFERENCES exercises(id) ON DELETE CASCADE,
    FOREIGN KEY(tag) REFERENCES tags(id) ON DELETE CASCADE
);

DROP TABLE IF EXISTS categories;
CREATE TABLE categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name STRING NOT NULL,
    parent INTEGER,
    FOREIGN KEY (parent) REFERENCES id
);