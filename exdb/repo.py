# -*- coding: utf-8 -*-
# Copyright 2013 Michael Helmling
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation

from os.path import dirname, join, exists, relpath
import os
import subprocess, shutil

def repoPath():
    import exdb
    return join(exdb.instancePath, "repo")

def templatePath():
    return join(repoPath(), "templates")

def exercisePath(exercise):
    """Return the directory inside the repository where *exercise* is (or should be) located."""
    return join(repoPath(), 'exercises', exercise.identifier())

def callHg(*args, **kwargs):
    if "cwd" not in kwargs:
        kwargs["cwd"] = repoPath()
    return subprocess.check_call(["hg"] + list(args), **kwargs)



def initRepository(path, overwrite=False):
    """Creates an initial hg repository at the given *path*.
    
    If *overwrite* is True and the path exists, it will be removed without warning.
    """
    path = repoPath()
    if exists(path):
        if overwrite:
            shutil.rmtree(path)
        else:
            return
    else:
        os.makedirs(path)
    callHg("init")
    for subdir in ("templates", "exercises"):
        os.mkdir(join(path, subdir))
        callHg("add", subdir)
    myDir = dirname(__file__)
    for texfile in "template.tex", "preamble.tex":
        shutil.copy(join(myDir, texfile), templatePath())
        callHg("add", join("templates", texfile))
    callHg("commit", "-u", "system", "-m", "Initial setup")

def addExercise(exercise, previews={}):
    """Adds the given exercise to the repository."""
    basePath = exercisePath(exercise)
    assert not exists(basePath)
    os.mkdir(basePath)
    xmlPath = join(basePath, exercise.identifier() + ".xml")
    with open(xmlPath, "wt") as f:
        f.write(exercise.toXML())
    commitMessage = "ADD {}".format(exercise.identifier())
    callHg("add", relpath(xmlPath, repoPath()))
    callHg("commit", "-u", exercise.creator, "-m", commitMessage)
    for filename, imagePath in previews.items():
        shutil.copyfile(imagePath, join(basePath, filename))
        shutil.rmtree(dirname(imagePath))
        
def updateExercise(exercise, previews={}):
    """Updates the given exercise"""
    basePath = exercisePath(exercise)
    assert exists(basePath)
    xmlPath = join(basePath, exercise.identifier() + ".xml")
    with open(xmlPath, "wt") as f:
        f.write(exercise.toXML())
    commitMessage = "EDIT {}".format(exercise.identifier())
    callHg("commit", "-u", exercise.creator, "-m", commitMessage)
    for filename, imagePath in previews.items():
        shutil.copyfile(imagePath, join(basePath, filename))
        shutil.rmtree(dirname(imagePath))