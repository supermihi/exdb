# -*- coding: utf-8 -*-
# Copyright 2013 Michael Helmling
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation

from __future__ import unicode_literals

from os.path import dirname, join, exists, relpath
import io, os
import subprocess, shutil

def repoPath():
    import exdb
    return join(exdb.instancePath, "repo")

def remoteUrl():
    return callHg("showconfig", "paths.default")

def templatePath():
    return join(repoPath(), "templates")

def exercisePath(exercise):
    """Return the directory inside the repository where *exercise* is (or should be) located."""
    return join(repoPath(), 'exercises', exercise.identifier())

def callHg(*args, **kwargs):
    if "cwd" not in kwargs:
        kwargs["cwd"] = repoPath()
    return subprocess.check_output(["hg"] + list(args), **kwargs)


def initRepository():
    """Creates an initial hg repository at the given *path*.
    """
    path = repoPath()
    if not exists(path):
        os.makedirs(path)
    hgChanges = False
    if not exists(join(path, ".hg")):
        callHg("init")
    for subdir in ("templates", "exercises"):
        if not exists(join(path, subdir)):
            os.mkdir(join(path, subdir))
            callHg("add", subdir)
    myDir = dirname(__file__)
    for texfile in "template.tex", "preamble.tex":
        if not exists(join(templatePath(), texfile)):
            shutil.copy(join(myDir, texfile), templatePath())
            callHg("add", join("templates", texfile))
            hgChanges = True
    if hgChanges:
        callHg("commit", "-u", "system", "-m", "Initial setup")


def addExercise(exercise):
    """Adds the given exercise to the repository."""
    basePath = exercisePath(exercise)
    assert not exists(basePath)
    os.mkdir(basePath)
    xmlPath = join(basePath, exercise.identifier() + ".xml")
    with io.open(xmlPath, "wt", encoding="utf-8") as f:
        f.write(exercise.toXML())
    commitMessage = "ADD {} {}".format(exercise.creator, exercise.number)
    callHg("add", relpath(xmlPath, repoPath()))
    callHg("commit", "-u", exercise.creator, "-m", commitMessage)
    pushIfRemote()
        
def updateExercise(exercise, user=None):
    """Updates the given exercise"""
    basePath = exercisePath(exercise)
    assert exists(basePath)
    xmlPath = join(basePath, exercise.identifier() + ".xml")
    with io.open(xmlPath, "wt", encoding="utf-8") as f:
        f.write(exercise.toXML())
    commitMessage = "EDIT {} {}".format(exercise.creator, exercise.number)
    callHg("commit", "-u", user or exercise.creator, "-m", commitMessage)
    pushIfRemote()
        
def removeExercise(creator, number, user=None):
    path = join(repoPath(), "exercises", "{}{}".format(creator, number))
    callHg("remove", relpath(path, repoPath()))
    commitMessage = "REMOVE {} {}".format(creator, number)
    callHg("commit", "-u", user or creator, "-m", commitMessage)
    if exists(path):
        shutil.rmtree(path)
    pushIfRemote()

def generatePreviews(exercise, old=None):
    from . import tex
    from datetime import datetime
    for type in "exercise", "solution":
        dct = exercise["tex_{}".format(type)]
        for lang, texcode in dct.items():
            if old is not None and old["tex_{}".format(type)][lang] == dct[lang]:
                print('no update for {} {}'.format(type, lang))
                continue
            targetPath = join(exercisePath(exercise), "{}_{}.png".format(type, lang))
            if not exists(targetPath) or datetime.fromtimestamp(os.path.getmtime(targetPath)) < exercise.modified:
                image = tex.makePreview(texcode, lang, exercise.tex_preamble)
                shutil.copy(image, targetPath)
                shutil.rmtree(dirname(image))

def pushIfRemote():
    ans = callHg("showconfig", "paths.default")
    if len(ans) > 3:
        callHg("push")
        
def history(maxEntries=10):
    ans = callHg("log", "--template", "{author}\t{date|isodate}\t{desc}\n", "-l", str(maxEntries))
    entries = []
    for line in ans.splitlines(False):
        author, date, description = line.split("\t")
        try:
            action, creator, number = description.split(" ")
            entries.append({"author": author, "date": date, "action": action, "creator": creator, "number": number})
        except ValueError:
            entries.append({"author": author, "date": date, "description": description})
    return entries