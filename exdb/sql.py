# -*- coding: utf-8 -*-
# Copyright 2013 Michael Helmling
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation

import sqlite3
import json
from os.path import dirname, exists, join
from .exercise import Exercise
from contextlib import contextmanager

def sqlPath():
    import exdb
    return join(exdb.instancePath, "database.sqlite")

def connect(database=None):
    if database is None:
        database = sqlPath()
    conn = sqlite3.connect(database)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    return conn

@contextmanager
def conditionalConnect(connection):
    if connection:
        conn = connection
    else:
        conn = connect()
    yield conn
    if not connection:
        conn.close()

def initDatabase(overwrite=False):
    """Initialize the database.
    
    Deletes all preexisting data if *overwrite* is True. Returns True if and only if the tables
    have been newly created.    
    """
    createTables = False
    if overwrite or not exists(sqlPath()):
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

def tags(conn):
    return [row[0] for row in conn.execute("SELECT tag FROM tags ORDER BY tag ASC")]

def updateTagsAndPreambles(exercise, exid, cursor):
    tagids = []
    for tag in exercise.tags:
        result = cursor.execute("SELECT id FROM tags WHERE tag=?", (tag,)).fetchone()
        if result is None:
            cursor.execute("INSERT INTO tags(tag) VALUES(?)", (tag,))
            tagid = cursor.lastrowid
        else:
            tagid = result["id"]
        tagids.append(tagid)
    cursor.executemany("INSERT INTO ex_tags_rel(exercise,tag) VALUES(?,?)", [ (exid,tagid) for tagid in tagids ])
    preambleids = []
    for preamble in exercise.tex_preamble:
        result = cursor.execute("SELECT id FROM preambles WHERE tex_preamble=?", (preamble,)).fetchone()
        if result is None:
            cursor.execute("INSERT INTO preambles(tex_preamble) VALUES(?)", (preamble,))
            preid = cursor.lastrowid
        else:
            preid = result["id"]
        preambleids.append(preid)
    cursor.executemany("INSERT INTO ex_pre_rel(exercise, preamble) VALUES(?,?)", [ (exid,preid) for preid in preambleids ])


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
        updateTagsAndPreambles(exercise, exid, cursor)
        conn.commit()

def updateExercise(exercise, connection=None):
    with conditionalConnect(connection) as conn:
        cursor = conn.cursor()
        id = cursor.execute("SELECT id FROM exercises WHERE creator=? AND number=?", (exercise.creator, exercise.number)).fetchone()[0]
        cursor.execute("DELETE FROM ex_tags_rel WHERE exercise=?", (id,))
        cursor.execute("DELETE FROM ex_pre_rel WHERE exercise=?", (id,))
        updateTagsAndPreambles(exercise, id, cursor)
        cursor.execute("UPDATE exercises SET description=?, modified=?, tex_exercise=?, tex_solution=? WHERE creator=? AND number=?",
                       [exercise.description, exercise.modified.strftime(exercise.DATEFMT),
                        json.dumps(exercise.tex_exercise), json.dumps(exercise.tex_solution),
                        exercise.creator, exercise.number])
        cursor.execute("DELETE FROM tags WHERE tags.id NOT IN  (SELECT tag FROM ex_tags_rel);")
        cursor.execute("DELETE FROM preambles WHERE preambles.id NOT IN  (SELECT preamble FROM ex_pre_rel);")
        conn.commit()


def removeExercise(creator, number, connection=None):
    with conditionalConnect(connection) as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM exercises WHERE creator=? AND number=?', (creator, number))
        cursor.execute("DELETE FROM tags WHERE tags.id NOT IN  (SELECT tag FROM ex_tags_rel);")
        cursor.execute("DELETE FROM preambles WHERE preambles.id NOT IN  (SELECT preamble FROM ex_pre_rel);")
        conn.commit()


def exercises(ids=None, connection=None):
    with conditionalConnect(connection) as conn:
        exercises = []
        def readTable(name, whereClause=""):
            dct = {}
            for row in conn.execute("SELECT * FROM {} {}".format(name, whereClause)):
                dct[row["id"]] = row
            return dct
        def readRelTable(name, attr):
            dct = {}
            for row in conn.execute("SELECT * FROM {}".format(name)):
                if row["exercise"] not in dct:
                    dct[row["exercise"]] = []
                dct[row["exercise"]].append(row[attr])
            return dct
        if ids:
            dbExercises = readTable("exercises", "WHERE id IN ({})".format(", ".join(str(id) for id in ids)))
        else:
            dbExercises = readTable("exercises")
        dbTags = readTable("tags")
        dbPreambles = readTable("preambles")
        dbTagsRel = readRelTable("ex_tags_rel", "tag")
        dbPreRel = readRelTable("ex_pre_rel", "preamble")
        for id, row in dbExercises.items():
            exercise = Exercise(creator=row["creator"], number=row["number"],
                                modified=row["modified"], description=row["description"],
                                tex_exercise=json.loads(row["tex_exercise"]), tex_solution=json.loads(row["tex_solution"]))
            if id in dbTagsRel:
                exercise.tags = [ dbTags[tagid]["tag"] for tagid in dbTagsRel[id]]
            if id in dbPreRel:
                exercise.tex_preamble = [ dbPreambles[preid]["tex_preamble"] for preid in dbPreRel[id] ]
            exercises.append(exercise)
    return exercises

def searchExercises(tags=[], connection=None):
    with conditionalConnect(connection) as conn:
        if len(tags) == 0:
            return exercises(connection=conn)
        result = conn.execute("SELECT exercise FROM ex_tags_rel WHERE tag IN (SELECT id FROM tags WHERE tag IN ({}))"
                             .format(', '.join('"{}"'.format(tag) for tag in tags)));
        ids = [ row[0] for row in result ]
        return exercises(ids=ids, connection=conn)

def exercise(creator, number, connection=None):
    with conditionalConnect(connection) as conn:
        ex = conn.execute("SELECT * FROM exercises WHERE creator=? AND number=?", (creator, number)).fetchone()
        if not ex:
            raise ValueError("No exercise found for creator {} and number {}".format(creator, number))
        tags = [row[0] for row in conn.execute("SELECT tag FROM tags WHERE id IN (SELECT tag FROM ex_tags_rel WHERE exercise=?)", (ex["id"],))]
        preambles = [row[0] for row in conn.execute("SELECT tex_preamble FROM preambles WHERE id IN (SELECT preamble FROM ex_pre_rel WHERE exercise=?)", (ex["id"],))]
        exercise = Exercise(creator=ex["creator"], number=ex["number"], modified=ex["modified"], description=ex["description"],
                            tex_exercise=json.loads(ex["tex_exercise"]), tex_solution=json.loads(ex["tex_solution"]),
                            tags=tags, tex_preamble=preambles)
    return exercise
    