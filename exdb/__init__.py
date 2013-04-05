# -*- coding: utf-8 -*-
# Copyright 2013 Michael Helmling
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation

from os.path import exists, join, relpath
from os import mkdir, makedirs, remove
import shutil
import subprocess

repoPath = sqlitePath = None

def init(instancepath):
    global repoPath, sqlitePath
    repoPath = join(instancepath, "repo")
    sqlitePath = join(instancepath, "database.sqlite")

def createInstance(path, reset=False):
    repo = join(path, "repo")
    sqlite = join(path, "database.sqlite")
    
    if exists(path):
        if reset:
            if exists(repo) and exists(join(repo, ".hg")):
                shutil.rmtree(repo)
            if exists(sqlite):
                remove(sqlite)
    else:
        makedirs(path)
    if not exists(repo):
        mkdir(repo)
        subprocess.check_call(["hg", "init"], cwd=repo)
        for subdir in ("templates", "exercises"):
            mkdir(join(repo, subdir))
        
    if not exists(sqlite):
        sql.createDb()
    init(path)

def exerciseDirectory(exercise):
    """Return the directory inside the repository where *exercise* is (or should be) located.
    
    The result is an absolute path.
    """
    return join(repoPath, 'exercises', exercise.identifier()) 

def addExercise(exercise):
    """Add an exercise to the repository."""
    sql.addExercise(exercise) # this creates the number also
    basePath = exerciseDirectory(exercise)
    assert not exists(basePath)
    mkdir(basePath)
    xmlPath = join(basePath, exercise.identifier() + ".xml")
    with open(xmlPath, "wt") as f:
        f.write(exercise.toXML())
    commitMessage = "ADD {}".format(exercise.identifier())
    subprocess.check_call(["hg", "add", relpath(xmlPath, repoPath)], cwd=repoPath)
    subprocess.check_call(["hg", "commit", "-u", exercise.creator, "-m", commitMessage], cwd=repoPath)
    
def exercises():
    """Returns a list of ALL exercises from the database."""
    return sql.exercises()
    
    
from . import sql