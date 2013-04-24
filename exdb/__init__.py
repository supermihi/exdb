# -*- coding: utf-8 -*-
# Copyright 2013 Michael Helmling
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation

from os.path import dirname, exists, join, relpath
from os import mkdir, makedirs, remove
import shutil
import subprocess
import datetime
import logging


instancePath = None
    
def populateDatabase():
    logging.info("populating database")
    import glob
    from .exercise import Exercise
    conn = sql.connect()
    for xmlPath in glob.glob(join(repo.repoPath(), "exercises", "*", "*.xml")):
        with open(xmlPath, "rt") as xmlFile:
            xml = xmlFile.read()
        exercise = Exercise.fromXMLString(xml)
        sql.addExercise(exercise, connection=conn)
    conn.close()

def init(path, overwrite=False):
    global instancePath
    instancePath = path
    if path is None:
        return
    if not exists(path):
        makedirs(path)
    repo.initRepository(overwrite=overwrite)
    previewPath = tex.previewPath()
    if exists(previewPath) and overwrite:
        shutil.rmtree(previewPath)
    if not exists(previewPath):
        mkdir(previewPath)
    if sql.initDatabase(overwrite):
        populateDatabase()

def addExercise(exercise, connection=None):
    """Add an exercise to the repository."""
    sql.addExercise(exercise, connection=connection) # this also sets exercise.number
    repo.addExercise(exercise)
    repo.generatePreviews(exercise)
    
def updateExercise(exercise, connection=None, user=None):
    assert exercise.number is not None
    assert exercise.creator is not None
    exercise.modified = datetime.datetime.now()
    sql.updateExercise(exercise, connection=connection)
    repo.updateExercise(exercise, user)
    repo.generatePreviews(exercise)

def removeExercise(creator, number, connection=None, user=None):
    sql.removeExercise(creator, number, connection=connection)
    repo.removeExercise(creator, number, user)

def exercises():
    """Returns a list of ALL exercises from the database."""
    return sql.exercises()
    
    
from . import repo, sql, tex