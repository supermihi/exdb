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

repoPath = None
sqlitePath = None

def init(repo, sqlite):
    global repoPath, sqlitePath
    repoPath = repo
    sqlitePath = sqlite
    
def makePlayground(path, reset=False):
    repo = join(path, "repo")
    sqlite = join(path, "test.sqlite")
    init(repo, sqlite)
    if exists(path):
        if reset:
            if exists(repoPath) and exists(join(repoPath, ".hg")):
                shutil.rmtree(repoPath)
            if exists(sqlitePath):
                remove(sqlitePath)
    else:
        makedirs(path)
    if not exists(repoPath):
        mkdir(repoPath)
        subprocess.check_call(["hg", "init"], cwd=repoPath)
    if not exists(sqlitePath):
        sql.createDb()

def addExercise(exercise):
    """Add an exercise to the repository."""
    sql.addExercise(exercise) # this creates the number also
    basePath = join(repoPath, exercise.identifier())
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