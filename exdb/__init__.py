# -*- coding: utf-8 -*-
# Copyright 2013 Michael Helmling
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation

from os.path import dirname, exists, join, relpath
from os import mkdir, makedirs, remove
import sys
import shutil
import subprocess
import datetime
import logging


instancePath = None
    
def populateDatabase():
    """Populate the SQLite database with exercises from the XML files in the repository.
    
    This assumes that the database does not exist or is empty; otherwise you will get consistency
    problems.
    """
    import glob
    from .exercise import Exercise
    conn = sql.connect()
    for xmlPath in glob.glob(join(repo.repoPath(), "exercises", "*", "*.xml")):
        xml = open(xmlPath, "rb").read()
        exercise = Exercise.fromXMLString(xml)
        sql.addExercise(exercise, connection=conn)
    conn.close()


def init(path):
    """Initialize the exdb package with instance directory *path*.
    
    This function intelligently creates the parts of the instance directory which do not yet exist:
    - the repository is initalized (if necessary) and populated with the initial directory
      structure. Tex templates are added and commited.
    - the preview path is created
    - the database is created and populated
    """
    global instancePath
    instancePath = path
    if path is None:
        return
    if not exists(path):
        makedirs(path)
    repo.initRepository()
    previewPath = join(instancePath, "previews")
    if not exists(previewPath):
        mkdir(previewPath)
    if sql.initDatabase():
        populateDatabase()
    tags.initTree(sql.tags())


def addExercise(exercise, connection=None):
    """Adds *exercise* to the repository and updates the database and previews.
    
    Uses the SQLite connection object *connection* if supplied.
    If the exercise does not yet have a number, it will be set by this method.
    """
    sql.addExercise(exercise, connection=connection)
    repo.addExercise(exercise)
    repo.generatePreviews(exercise)


def updateExercise(exercise, connection=None, user=None, old=None):
    """Updates *exercise* in repository and database.
    
    Uses the SQLite *connection* if possible. If *user* is given, that value is used as
    commit author in the repository; otherwise exercise.creator is used.
    
    The *old* exercise can be given to prevent unnecessary TeX recompilation: When the
    TeX code in the new and old exercise coincides, no new image is compiled.
    """
    exercise.modified = datetime.datetime.now()
    sql.updateExercise(exercise, connection=connection)
    repo.updateExercise(exercise, user)
    repo.generatePreviews(exercise, old)


def removeExercise(creator, number, connection=None, user=None):
    """Removes the exercise identified by *creator* and *number* from repo and database.
    
    If *user* is given, it is used as hg commit author; otherwise that is set to *creator*. 
    """
    sql.removeExercise(creator, number, connection=connection)
    repo.removeExercise(creator, number, user)

def uni(string):
    if sys.version_info.major >= 3 or type(string) is unicode:
        return string
    return string.decode('utf-8')

from . import repo, sql, tags, tex