# -*- coding: utf-8 -*-
# Copyright 2013 Michael Helmling
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation

import sqlite3
import json
from os.path import dirname, join
from .exercise import Exercise

dbPath = None

def connect(database=None):
    if database is None:
        database = dbPath
    conn = sqlite3.connect(dbPath)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    return conn

def createDb():
    """Creates the initial database. WARNING this deletes all data."""
    with connect() as db:
        with open(join(dirname(__file__), 'dbschema.sql'), "rt") as schema:
            db.cursor().executescript(schema.read())
    db.close()
    
def addExercise(exercise):
    assert exercise.number is None
    conn = connect()
    maxnr = conn.execute("SELECT MAX(number) FROM exercises WHERE creator=?", (exercise.creator,)).fetchone()[0]
    exercise.number = 1 if maxnr is None else maxnr + 1
    cursor = conn.cursor()
    cursor.execute("INSERT INTO exercises(creator, number, description, modified, "
                 "tex_exercise, tex_solution) VALUES(?, ?, ?, ?, ?, ?)",
                 [exercise.creator, exercise.number, exercise.description, exercise.modified,
                  json.dumps(exercise.tex_exercise, ensure_ascii=False),
                  json.dumps(exercise.tex_solution, ensure_ascii=False)])
    exid = cursor.lastrowid
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
    conn.commit()
    conn.close()
        
def exercises():
    conn = connect()
    exercises = []
    def readTable(name):
        dct = {}
        for row in conn.execute("SELECT * FROM {}".format(name)):
            dct[row["id"]] = row
        return dct
    def readRelTable(name, attr):
        dct = {}
        for row in conn.execute("SELECT * FROM {}".format(name)):
            if row["exercise"] not in dct:
                dct[row["exercise"]] = []
            dct[row["exercise"]].append(row[attr])
        return dct
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