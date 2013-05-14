# -*- coding: utf-8 -*-
# Copyright 2013 Michael Helmling
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation

import sqlite3
import json
from os.path import dirname, exists, join
from itertools import product
from collections import OrderedDict
from contextlib import contextmanager

from .exercise import Exercise



def sqlPath():
    """Return the absolute path of the sqlite database."""
    import exdb
    return join(exdb.instancePath, "database.sqlite")


def connect():
    """Connect to the database and return the connection object."""
    conn = sqlite3.connect(sqlPath())
    conn.execute("PRAGMA foreign_keys = ON;")
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
    """Initialize the database.
    
    Returns True if and only if the tables have been newly created.    
    """
    createTables = False
    if not exists(sqlPath()):
        createTables = True
    else:
        with connect() as db:
            ans = set(row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table';"))
            if "exercises" not in ans:
                createTables = True
    if createTables:    
        with connect() as db:
            with open(join(dirname(__file__), 'dbschema.sql'), "rt") as schema:
                db.cursor().executescript(schema.read())
        db.close()
    return createTables

def addMissingTags(exid, cursor):
    result = cursor.execute("SELECT tag FROM exercises_tags "
                                "WHERE exercise = ? "
                                "AND tag NOT IN (SELECT name FROM tags WHERE is_tag=1)", (exid,))
    newTags = [row[0] for row in result]
    if len(newTags):
        uncatId = cursor.execute("SELECT id FROM tags "
                                 "WHERE is_tag=0 "
                                 "AND parent ISNULL "
                                 "AND mat_path='.' "
                                 "AND name='uncategorized'").fetchone()[0]
        cursor.executemany("INSERT INTO tags(name, is_tag, parent, mat_path) "
                           "VALUES(?, 1, ?, ?)", product(newTags, [uncatId], [".{}.".format(uncatId)]))
    
def addExercise(exercise, connection=None):
    with conditionalConnect(connection) as conn:
        if exercise.number is None:
            maxnr = conn.execute("SELECT MAX(number) FROM exercises WHERE creator=?", (exercise.creator,)).fetchone()[0]
            exercise.number = 1 if maxnr is None else maxnr + 1
        cursor = conn.cursor()
        cursor.execute("INSERT INTO exercises(creator, number, description, modified, "
                     "tex_exercise, tex_solution) VALUES(?, ?, ?, ?, ?, ?)",
                     [exercise.creator, exercise.number, exercise.description, exercise.modified.strftime(exercise.DATEFMT),
                      json.dumps(exercise.tex_exercise, ensure_ascii=False),
                      json.dumps(exercise.tex_solution, ensure_ascii=False)])
        exid = cursor.lastrowid
        cursor.executemany("INSERT INTO exercises_preambles(exercise, preamble) VALUES(?,?)",
                           [ (exid,preamble) for preamble in exercise.tex_preamble])
        cursor.executemany("INSERT INTO exercises_tags(exercise,tag) VALUES(?,?)",
                           [ (exid,tag) for tag in exercise.tags ])
        addMissingTags(exid, cursor)
        conn.commit()


def updateExercise(exercise, connection=None):
    with conditionalConnect(connection) as conn:
        cursor = conn.cursor()
        id = cursor.execute("SELECT id FROM exercises WHERE creator=? AND number=?",
                            (exercise.creator, exercise.number)).fetchone()[0]
        cursor.execute("DELETE FROM exercises_preambles WHERE exercise=?", (id,))
        cursor.executemany("INSERT INTO exercises_preambles(exercise, preamble) VALUES(?,?)",
                           [ (id,preamble) for preamble in exercise.tex_preamble])
        cursor.execute("UPDATE exercises SET description=?, modified=?, tex_exercise=?, tex_solution=? "
                       "WHERE creator=? AND number=?",
                       [exercise.description, exercise.modified.strftime(exercise.DATEFMT),
                        json.dumps(exercise.tex_exercise), json.dumps(exercise.tex_solution),
                        exercise.creator, exercise.number])
        cursor.execute("DELETE FROM exercises_tags WHERE exercise=?", (id,))
        cursor.executemany("INSERT INTO exercises_tags(exercise,tag) VALUES(?,?)",
                       [ (id, tag) for tag in exercise.tags])
        cursor.execute("DELETE FROM tags WHERE is_tag=1 AND name NOT IN  (SELECT tag FROM exercises_tags);")
        addMissingTags(id, cursor)
        conn.commit()


def removeExercise(creator, number, connection=None):
    with conditionalConnect(connection) as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM exercises WHERE creator=? AND number=?', (creator, number))
        cursor.execute("DELETE FROM tags WHERE is_tag=1 AND name NOT IN (SELECT tag FROM exercises_tags);")
        conn.commit()


def exercises(ids=None, connection=None):
    with conditionalConnect(connection) as conn:
        def readTable(name, whereClause="", multi=False):
            dct = OrderedDict()
            for row in conn.execute("SELECT * FROM {} {}".format(name, whereClause)):
                if multi:
                    if row[0] in dct:
                        dct[row[0]].append(row[1])
                    else:
                        dct[row[0]] = [ row[1] ]
                else:  
                    dct[row[0]] = row
            return dct
        if ids:
            dbExercises = readTable("exercises", whereClause="WHERE id IN ({})".
                                    format(", ".join(str(id) for id in ids)))
        else:
            dbExercises = readTable("exercises")
        exercises = []
        dbTags = readTable("exercises_tags", multi=True)
        dbPreambles = readTable("exercises_preambles", multi=True)
        for id, row in dbExercises.items():
            exercise = Exercise(creator=row["creator"], number=row["number"],
                                modified=row["modified"], description=row["description"],
                                tex_exercise=json.loads(row["tex_exercise"]),
                                tex_solution=json.loads(row["tex_solution"]))
            if id in dbTags:
                exercise.tags = dbTags[id]
            if id in dbPreambles:
                exercise.tex_preamble = dbPreambles[id]
            exercises.append(exercise)
    return exercises

def searchExercises(tags=[], cats=[], langs=[], description="", connection=None):
    with conditionalConnect(connection) as conn:
        args = []
        selects = []
        if len(tags):
            selects.append("SELECT exercise FROM exercises_tags\n" \
                           "    WHERE {}\n" \
                           "    GROUP BY exercise" \
                           "    HAVING COUNT(*) = ?".format(" OR ".join(["tag=?"]*len(tags))))
            args.extend(tags + [len(tags)])
        for id, mat_path in cats:
            selects.append("SELECT exercise FROM exercises_tags WHERE tag IN\n"
                           "    (SELECT name FROM tags WHERE is_tag AND mat_path LIKE '{}{}.%') GROUP BY exercise"
                           .format(mat_path, id))
        if description != "":
            selects.append('SELECT id FROM exercises WHERE description LIKE "%{}%"'.format(description))
        if len(selects):
            print(" UNION ".join(selects))
            print(args)
            ids = [row[0] for row in conn.execute(" UNION ".join(selects), args)]
            print(ids)
            if len(ids) == 0:
                return []
        else:
            ids = None
        exes = exercises(ids=ids, connection=conn)
        if len(langs) > 0:
            exes = [e for e in exes if all(lang in e.tex_exercise for lang in langs)]
        return exes

def exercise(creator, number, connection=None):
    with conditionalConnect(connection) as conn:
        ex = conn.execute("SELECT * FROM exercises WHERE creator=? AND number=?", (creator, number)).fetchone()
        tags = [row[0] for row in conn.execute("SELECT tag FROM exercises_tags "
                                               "WHERE exercise=?", (ex["id"],))]
        preambles = [row[0] for row in conn.execute("SELECT preamble FROM exercises_preambles "
                                                    "WHERE exercise=?", (ex["id"],))]
        exercise = Exercise(creator=ex["creator"], number=ex["number"], modified=ex["modified"],
                            description=ex["description"],
                            tex_exercise=json.loads(ex["tex_exercise"]),
                            tex_solution=json.loads(ex["tex_solution"]),
                            tags=tags, tex_preamble=preambles)
    return exercise
    