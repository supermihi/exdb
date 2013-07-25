# -*- coding: utf-8 -*-
# Copyright 2013 Michael Helmling
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation

import json, sqlite3
import re
from os.path import dirname, exists, join
from itertools import product
from collections import OrderedDict
from contextlib import contextmanager
from datetime import datetime

from .exercise import Exercise


def sqlPath():
    """Return the absolute path of the sqlite database."""
    import exdb
    return join(exdb.instancePath, "database.sqlite")


def regexp(expr, item):
    """The REGEXP function callback for SQLite."""
    reg = re.compile(expr, flags=re.MULTILINE)
    return reg.search(item) is not None


def icontains(base, search):
    """Performs a case-insensitive search of *search* string in the *base* string.
    
    *search* is first split by whitespaces. Then the function returns True iff every piece is 
    contained (ignoring case) in *base*."""
    return all(bit.lower() in base.lower() for bit in search.split())


def dumpTexDict(code):
    """Dump given lang-to-texcode dictionary (exercise or solution) to a JSON string."""
    return json.dumps(code, ensure_ascii=False, sort_keys=True, indent=2)

sqlite3.register_adapter(dict, dumpTexDict)
sqlite3.register_adapter(datetime, lambda date: date.strftime(Exercise.DATEFMT))


def parseTexDict(dump):
    return json.loads(dump)

sqlite3.register_converter("TEXDICT", parseTexDict)
sqlite3.register_converter("DATETIME", lambda s: datetime.strptime(s, Exercise.DATEFMT))


def connect():
    """Connect to the database and return the connection object."""
    conn = sqlite3.connect(sqlPath(), detect_types=sqlite3.PARSE_DECLTYPES)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.create_function("REGEXP", 2, regexp)
    conn.create_function("CONTAINS", 2, icontains)
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def conditionalConnect(connection):
    """Context manager returning a SQLite connection.
    
    Yields *connection* if it is not None; otherwise, a new connection is established. In the 
    latter case, the connection is closed after exiting the with statement.
    """
    conn = connection or connect()    
    yield conn
    if not connection:
        conn.close()


def initDatabase():
    """Initialize the database. Returns whether or not the tables have been newly created."""
    if exists(sqlPath()):
        with connect() as db:
            if db.execute("SELECT count(*) FROM sqlite_master "
                          "WHERE type='table' AND name='exercises'").fetchone()[0]:
                return False
    with connect() as db:
        with open(join(dirname(__file__), 'dbschema.sql'), "rt") as schema:
            db.cursor().executescript(schema.read())
    db.close()
    return True


def tags(conn):
    """Return a flat list of available tags."""
    return [r[0] for r in conn.execute("SELECT name FROM tags WHERE is_tag")]
        

def addMissingTags(exid, cursor):
    """Adds missing tags in exercise with id *exid* to the database (under 'uncategorized').
    """
    result = cursor.execute("SELECT tag FROM exercises_tags WHERE exercise = ? AND tag NOT IN "
                            "(SELECT name FROM tags WHERE is_tag)", (exid,))
    newTags = [row[0] for row in result]
    if len(newTags):
        uncatId = cursor.execute("SELECT id FROM tags "
                                 "WHERE NOT is_tag AND mat_path='.' AND name='uncategorized'"
                                 ).fetchone()[0]
        cursor.executemany("INSERT INTO tags(name, is_tag, mat_path) "
                           "VALUES (?,1,?)", product(newTags, [".{}.".format(uncatId)]))


def addExercise(exercise, connection=None, deferCommit=False):
    """Adds the given exercise to the database."""
    with conditionalConnect(connection) as conn:
        if exercise.number is None:
            maxnr = conn.execute("SELECT MAX(number) FROM exercises WHERE creator=?",
                                 (exercise.creator,)).fetchone()[0]
            exercise.number = 1 if maxnr is None else maxnr + 1
        cursor = conn.cursor()
        cursor.execute("INSERT INTO exercises(creator, number, description, modified, "
                     "tex_exercise, tex_solution) VALUES (?,?,?,?,?,?)",
                     [exercise.creator, exercise.number, exercise.description,
                      exercise.modified, exercise.tex_exercise, exercise.tex_solution])
        exid = cursor.lastrowid
        cursor.executemany("INSERT INTO exercises_preambles(exercise, preamble) VALUES (?,?)",
                           [ (exid, preamble) for preamble in exercise.tex_preamble ])
        cursor.executemany("INSERT INTO exercises_files(exercise, filename) VALUES (?,?)",
                           [ (exid, filename) for filename in exercise.data_files ])
        cursor.executemany("INSERT INTO exercises_tags(exercise,tag) VALUES (?,?)",
                           [ (exid,tag) for tag in exercise.tags ])
        addMissingTags(exid, cursor)
        if not deferCommit:
            conn.commit()


def removeUnreferencedTags(curs):
    """Removes from the tags table all tags that are not referenced in any exercise.""" 
    curs.execute("DELETE FROM tags WHERE is_tag AND name NOT IN (SELECT tag FROM exercises_tags)")


def updateExercise(exercise, connection=None):
    """Update the database with modified *exercise*."""
    with conditionalConnect(connection) as conn:
        cursor = conn.cursor()
        id = cursor.execute("SELECT id FROM exercises WHERE creator=? AND number=?",
                            (exercise.creator, exercise.number)).fetchone()[0]
        cursor.execute("DELETE FROM exercises_preambles WHERE exercise=?", (id,))
        cursor.executemany("INSERT INTO exercises_preambles(exercise, preamble) VALUES(?,?)",
                           [ (id,preamble) for preamble in exercise.tex_preamble])
        cursor.execute("DELETE FROM exercises_files WHERE exercise=?", (id,))
        cursor.executemany("INSERT INTO exercises_files(exercise, filename) VALUES (?,?)",
                           [ (id, filename) for filename in exercise.data_files ])
        cursor.execute("UPDATE exercises "
                       "SET description=?, modified=?, tex_exercise=?, tex_solution=? "
                       "WHERE creator=? AND number=?",
                       [exercise.description, exercise.modified, exercise.tex_exercise,
                        exercise.tex_solution, exercise.creator, exercise.number])
        cursor.execute("DELETE FROM exercises_tags WHERE exercise=?", (id,))
        cursor.executemany("INSERT INTO exercises_tags(exercise,tag) VALUES(?,?)",
                       [ (id, tag) for tag in exercise.tags])
        removeUnreferencedTags(cursor)
        addMissingTags(id, cursor)
        conn.commit()


def removeExercise(creator, number, connection=None):
    """Remove the exercise with the given creator and number."""
    with conditionalConnect(connection) as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM exercises WHERE creator=? AND number=?', (creator, number))
        removeUnreferencedTags(cursor)
        conn.commit()


def exercises(ids=None, pagination=None, connection=None):
    """Return the list of exercises with the given *ids*."""
    with conditionalConnect(connection) as conn:
        def readTable(name, where="", order="", multi=False):
            dct = OrderedDict()
            for row in conn.execute("SELECT * FROM {} {} {}".format(name, where, order)):
                if multi:
                    if row[0] in dct:
                        dct[row[0]].append(row[1])
                    else:
                        dct[row[0]] = [ row[1] ]
                else:  
                    dct[row[0]] = row
            return dct
        if ids:
            idList = ", ".join(str(id) for id in ids)
            whereClause = "WHERE id IN ({})".format(idList)
            whereClause2 = "WHERE exercise IN ({})".format(idList)
        else:
            whereClause = whereClause2 = ""
        if pagination is None:
            pagination = {}
        orderby = pagination.get("orderby", "modified")
        direction = "DESC" if pagination.get("descending") else "ASC"
        limit = pagination.get("limit", -1)
        offset = pagination.get("offset", 0)
        orderClause="ORDER BY {} {} LIMIT {} OFFSET {}".format(orderby, direction, limit, offset)
        dbExercises = readTable("exercises", whereClause, orderClause)
        exercises = []
        dbTags = readTable("exercises_tags", whereClause2, multi=True)
        dbPreambles = readTable("exercises_preambles", whereClause2, multi=True)
        dbFilenames = readTable("exercises_files", whereClause2, multi=True)
        for id, row in dbExercises.items():
            exercise = Exercise(creator=row["creator"], number=row["number"],
                                modified=row["modified"], description=row["description"],
                                tex_exercise=row["tex_exercise"], tex_solution=row["tex_solution"])
            if id in dbTags:
                exercise.tags = dbTags[id]
            if id in dbPreambles:
                exercise.tex_preamble = dbPreambles[id]
            if id in dbFilenames:
                exercise.data_files = dbFilenames[id]
            exercises.append(exercise)
    return exercises


def searchExercises(connection=None, **kwargs):
    with conditionalConnect(connection) as conn:
        args = []
        selects = []
        if kwargs.get("tags", []):
            tags = kwargs["tags"]
            selects.append("SELECT exercise FROM exercises_tags\n" \
                           "    WHERE {}\n" \
                           "    GROUP BY exercise" \
                           "    HAVING COUNT(*) = ?".format(" OR ".join(["tag=?"]*len(tags))))
            args.extend(tags + [len(tags)])
        for id, mat_path in kwargs.get("cats", {}):
            selects.append("SELECT exercise FROM exercises_tags WHERE tag IN"
                           "  (SELECT name FROM tags WHERE is_tag AND mat_path LIKE '{}{}.%')"
                           "  GROUP BY exercise".format(mat_path, id))
        if kwargs.get("description", "") != "" or len(kwargs.get("langs", [])):
            exwheres = []
            if kwargs.get("description", "") != "":
                args.append(kwargs["description"])
                exwheres.append('CONTAINS(description, ?)')
            for lang in kwargs.get("langs", []):
                exwheres.append("tex_exercise REGEXP '^  \"{}\": \"'".format(lang))
            selects.append('SELECT id FROM exercises WHERE {}'.format(" AND ".join(exwheres)))
        if len(selects):
            query = " UNION ".join(selects)
            ids = [ row[0] for row in conn.execute(query, args) ]
            count = len(ids)
            if not count:
                return 0, []
        else:
            ids = None
            count = conn.execute("SELECT COUNT(*) FROM exercises").fetchone()[0]
        return count, exercises(ids=ids, pagination=kwargs.get("pagination", {}), connection=conn)


def exercise(creator, number, connection=None):
    """Return the exercise with given *creator* and *number*."""
    with conditionalConnect(connection) as conn:
        ex = conn.execute("SELECT * FROM exercises WHERE creator=? AND number=?",
                          (creator, number)).fetchone()
        tags = [row[0] for row in conn.execute("SELECT tag FROM exercises_tags "
                                               "WHERE exercise=?", (ex["id"],))]
        preambles = [row[0] for row in conn.execute("SELECT preamble FROM exercises_preambles "
                                                    "WHERE exercise=?", (ex["id"],))]
        files = [row[0] for row in conn.execute("SELECT filename FROM exercises_files "
                                                "WHERE exercise=?", (ex["id"],))] 
        exercise = Exercise(creator=ex["creator"], number=ex["number"], modified=ex["modified"],
                            description=ex["description"], tex_exercise=ex["tex_exercise"],
                            tex_solution=ex["tex_solution"], tags=tags, tex_preamble=preambles,
                            data_files=files)
    return exercise
