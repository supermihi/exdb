# -*- coding: utf-8 -*-
# Copyright 2013 Michael Helmling
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation

from os.path import dirname, exists, join, normpath
from os import mkdir, makedirs
import sys
import subprocess
import datetime
import logging

instancePath = None


def init(path, repository=None, level=logging.INFO):
    """Initialize the exdb package with instance directory `path`.
    
    This function intelligently creates those parts of the instance directory that don't yet exist:
    - if the ``repo`` subdirectory does not exist or does not contain a hg repository, it is
      initalized and populated with the initial directory structure. TeX templates are added and
      commited. If the `repository` argument is given, the repository is cloned from that URI
      instead.
    - the directory for temporary preview images is created
    - the database is created and populated
    - preview images are generated
    """
    if path is None:
        return
    global instancePath
    instancePath = path
    logging.basicConfig(level=level)
    if not exists(path):
        logging.info('Creating previously non-existing instance directory "{}"'.format(path))
        makedirs(path)
    repo.initRepository(repository)
    previewPath = join(instancePath, "previews")
    if not exists(previewPath):
        mkdir(previewPath)
    if sql.initDatabase():
        logging.info('Initializing SQLite database')
        populateDatabase()
    for exercise in sql.exercises():
        repo.compileSnippets(exercise, {}, init=True)
  

def version(packageName="exdb", packageDir=dirname(__file__)):
    """Returns the version of this git managed software package.

    If this __init__ file is located inside a git repository, then the output of a call to
    "git describe --dirty" is returned. Otherwise, the version is found through pkg_resources.
    """
    rootDir = normpath(join(packageDir, '..'))
    if exists(join(rootDir, '.git')):
        out = subprocess.check_output(['git', 'describe', '--dirty'], cwd=rootDir)
        return out.decode().strip()
    import pkg_resources
    return pkg_resources.get_distribution(packageName).version


def populateDatabase():
    """Populate the SQLite database with exercises from the XML files in the repository.
    
    This assumes that the database does not exist or is empty; otherwise you will get consistency
    problems.
    """
    import glob
    from .exercise import Exercise
    conn = sql.connect()
    tags.initTagsTable(conn)
    for xmlPath in sorted(glob.glob(join(repo.repoPath(), "exercises", "*", "*.xml"))):
        logging.info("reading exercise {}".format(xmlPath))
        exercise = Exercise.fromXMLFile(xmlPath)
        #xml = open(xmlPath, "rb").read()
        #exercise = Exercise.fromXMLString(xml)
        sql.addExercise(exercise, connection=conn, deferCommit=True)
    conn.commit()
    conn.close()


def addExercise(exercise, files, connection=None):
    """Adds *exercise* to the repository and updates the database and previews.
    
    If the exercise contains external data files, *files* must be a list of (filename, data)
    tuples.
    Uses the SQLite connection object *connection* if supplied.
    If the exercise does not yet have a number, it will be set by this method.
    """
    exercise.validate()
    repo.compileSnippets(exercise, files)
    with sql.conditionalConnect(connection) as conn:
        sql.addExercise(exercise, connection=conn)
        tags.storeTree(tags.readTreeFromTable(conn)) 
    repo.addExercise(exercise, files)


def updateExercise(exercise, files, old, connection=None, user=None):
    """Updates *exercise* in repository and database.
    
    Uses the SQLite *connection* if possible. If *user* is given, that value is used as
    commit author in the repository; otherwise exercise.creator is used.
    """
    exercise.validate()
    repo.compileSnippets(exercise, files, old)
    exercise.modified = datetime.datetime.now()
    with sql.conditionalConnect(connection) as conn:    
        sql.updateExercise(exercise, connection=conn)
        tags.storeTree(tags.readTreeFromTable(conn))
    repo.updateExercise(exercise, files, old, user=user)


def removeExercise(creator, number, connection=None, user=None):
    """Removes the exercise identified by *creator* and *number* from repo and database.
    
    If *user* is given, it is used as hg commit author; otherwise that is set to *creator*. 
    """
    with sql.conditionalConnect(connection) as conn:
        sql.removeExercise(creator, number, connection=conn)
        tags.storeTree(tags.readTreeFromTable(conn))
    repo.removeExercise(creator, number, user)


def updateTagTree(old, new, user, connection=None):
    """Store any changes in the tag tree (restructuring, renaming or deleting tags, ...).
    """
    if tags.compareTrees(old, new):
        return False
    oldTags = {}
    renames = {}
    deletes = set()
    newTagsIds = set([int(node.get("id")) for node in new.iter("tag")])
    for node in old.iter("tag"):
        id = int(node.get("id"))
        oldTags[id] = node.get("name")
        if id not in newTagsIds:
            deletes.add(node.get("name"))
    for node in new.iter("tag"):
        id = int(node.get("id"))
        if oldTags[id] != node.get("name"):
            renames[oldTags[id]] =  node.get("name")
    with sql.conditionalConnect(connection) as conn:
        if len(renames) + len(deletes):
            exercises = sql.exercises(connection=conn)
            for exercise in exercises:
                changed = False
                tagsFiltered = [t for t in exercise.tags if t not in deletes]
                if len(tagsFiltered) != len(exercise.tags):
                    exercise.tags = tagsFiltered
                    changed = True
                for i in range(len(exercise.tags)):
                    if exercise.tags[i] in renames:
                        changed = True
                        exercise.tags[i] = renames[exercise.tags[i]]
                if changed:
                    sql.updateExercise(exercise, connection=conn)
                    repo.storeExerciseXML(exercise)
        tags.storeTree(new)
        tags.initTagsTable(conn)
    repo.updateTagTree(renames, user)
    return True


def uni(string):
    """Ensure given string is unicode; works for python2 and python3."""
    if sys.version_info.major >= 3 or type(string) is unicode:
        return string
    return string.decode('utf-8')


from exdb import repo, sql, tags, tex