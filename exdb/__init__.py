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


instancePath = None

def init(instancepath):
    global instancePath
    instancePath = instancepath

def createInstance(path, overwrite=False):
    init(path)
    if not exists(path):
        makedirs(path)
    repo.initRepository(overwrite)
    previewPath = tex.previewPath()
    if exists(previewPath) and overwrite:
        shutil.rmtree(previewPath)
    if not exists(previewPath):
        
        mkdir(previewPath)
    sql.initDatabase(overwrite)

def addExercise(exercise, createPreviews=True):
    """Add an exercise to the repository."""
    if createPreviews:
        previews = exercise.createPreviews()
    else:
        previews = None
    sql.addExercise(exercise) # this also sets exercise.number
    repo.addExercise(exercise, previews)
    
    
def exercises():
    """Returns a list of ALL exercises from the database."""
    return sql.exercises()
    
    
from . import repo, sql, tex