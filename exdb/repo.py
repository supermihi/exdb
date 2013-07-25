# -*- coding: utf-8 -*-
# Copyright 2013 Michael Helmling
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation

from __future__ import unicode_literals

import io, os, subprocess, shutil
from os.path import dirname, join, exists, relpath
from datetime import datetime


def repoPath():
    """The absolute path of the hg repository."""
    import exdb
    return join(exdb.instancePath, "repo")


def remoteUrl():
    """The remote URL of the repository, if configured."""
    return callHg("showconfig", "paths.default")


def templatePath():
    """The absolute path of the LaTeX template directory."""
    return join(repoPath(), "templates")


def exercisePath(exercise=None, creator=None, number=None):
    """Directory inside the repository where the given exercise is (or should be) located.
    
    The exercise may be either given as Exercise object *exercise* or by *creator* and 
    *number*.
    """
    if exercise is not None:
        identifier = exercise.identifier()
    else:
        identifier = "{}{}".format(creator, number)
    return join(repoPath(), 'exercises', identifier)


def callHg(*args, **kwargs):
    """Calls the hg script in the repo directory with given args.
    
    Any keyword arguments are passed to the subprocess.check_output function call.
    """
    if "cwd" not in kwargs:
        kwargs["cwd"] = repoPath()
    return subprocess.check_output(["hg"] + list(args), **kwargs)


def initRepository():
    """Ensure that an initial exercise repository exists.
    
    Calls "hg init" if necessary, adds missing templates, creates a bare tagCategories.xml, and
    commits any changes.    
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
    tagCatFile = join(path, "tagCategories.xml")
    if not exists(tagCatFile):
        from . import tags
        tags.storeTree(tags.initialTree())
        callHg("add", tagCatFile)
    if hgChanges:
        callHg("commit", "-u", "system", "-m", "Initial setup")
        pushIfRemote()


def addExercise(exercise, files=None):
    """Adds the given exercise to the repository.
    
    If it contains data files, *files* has to be a list of (filename, data) tuples.
    """
    basePath = exercisePath(exercise)
    os.mkdir(basePath)
    xmlPath = join(basePath, exercise.identifier() + ".xml")
    with io.open(xmlPath, "wt", encoding="utf-8") as f:
        f.write(exercise.toXML())
    callHg("add", relpath(xmlPath, repoPath()))
    for fname, fdata in files or []:
        fPath = join(basePath, fname)
        with open(fPath, "wb") as f:
            f.write(fdata)
        callHg("add", relpath(fPath, repoPath()))            
    commitMessage = "ADD {} {}".format(exercise.creator, exercise.number)
    callHg("commit", "-u", exercise.creator, "-m", commitMessage)
    pushIfRemote()
    

def loadFiles(creator, number, filenames):
    """Load image files with names *filenames* for the specified exercise.
    
    Returns a list of (filename, data) tuples.
    """
    exPath = exercisePath(creator=creator, number=number)
    files = []
    for name in filenames:
        data = open(join(exPath, name), "rb").read()
        files.append( (name, data) )
    return files
    
    
def storeExerciseXML(exercise):
    """Write the XML file encoding the given exercise to the appropriate path."""
    basePath = exercisePath(exercise)
    xmlPath = join(basePath, exercise.identifier() + ".xml")
    with io.open(xmlPath, "wt", encoding="utf-8") as f:
        f.write(exercise.toXML())


def updateExercise(exercise, files=None, old=None, user=None):
    """Updates the given exercise: writes XML file and commits the repository."""
    basePath = exercisePath(exercise)
    if old is None:
        from exdb.exercise import Exercise
        old = Exercise.fromXMLFile(join(basePath, exercise.identifier() + ".xml"))
    # delete removed data files from the repository
    for removedFile in set(old.data_files) - set(exercise.data_files):
        callHg("remove", relpath(join(basePath, removedFile), repoPath()))
    # add newly uploaded files (or overwrite existing ones)
    for fname, fdata in files:
        fPath = join(basePath, fname)
        with open(fPath, "wb") as f:
            f.write(fdata)
        if fname not in old.data_files:
            callHg("add", relpath(fPath, repoPath()))
    storeExerciseXML(exercise)
    commitMessage = "EDIT {} {}".format(exercise.creator, exercise.number)
    callHg("commit", "-u", user or exercise.creator, "-m", commitMessage)
    pushIfRemote()


def removeExercise(creator, number, user=None):
    """Remove an exercise by deleting its path from the repository."""
    path = join(repoPath(), "exercises", "{}{}".format(creator, number))
    callHg("remove", relpath(path, repoPath()))
    commitMessage = "REMOVE {} {}".format(creator, number)
    callHg("commit", "-u", user or creator, "-m", commitMessage)
    if exists(path):
        shutil.rmtree(path)
    pushIfRemote()


def updateTagTree(renames, user):
    """Commit changes to the tag tree and push, if a remote repo exists."""
    callHg("commit", "-u", user, "-m", "TAGS")
    pushIfRemote()


def generatePreviews(exercise, old=None):
    """Generate preview images for the given *exercise*.
    
    This creates files of the form foo1/solution_EN.png for all existing tex snippets.
    *old* may be a previous exercise object; in that case, previews are generated only for those
    snippets which have changed compared to *old*.
    """
    from . import tex
    files = loadFiles(exercise.creator, exercise.number, exercise.data_files)
    for textype in "exercise", "solution":
        dct = exercise["tex_{}".format(textype)]
        for lang, texcode in dct.items():
            if old and old.tex_preamble == exercise.tex_preamble:
                try:
                    if old["tex_" + textype][lang] == texcode:
                        continue
                except KeyError:
                    pass
            targetPath = join(exercisePath(exercise), "{}_{}.png".format(textype, lang))
            if not exists(targetPath) or datetime.fromtimestamp(os.path.getmtime(targetPath)) < exercise.modified:
                image = tex.makePreview(texcode, lang, exercise.tex_preamble, files)
                shutil.copy(image, targetPath)
                shutil.rmtree(dirname(image))


def pushIfRemote():
    """Push the repository if a remote address is configured."""
    ans = callHg("showconfig", "paths.default")
    if len(ans) > 3:
        callHg("push")


def history(maxEntries=10):
    ans = callHg("log", "--template", "{author}\t{date|isodate}\t{desc}\n", "-l", str(maxEntries))
    entries = []
    for line in ans.splitlines(False):
        author, date, description = line.split("\t")
        descriptionParts = description.split(" ")
        action = descriptionParts[0]
        entry = {"author": author, "date": date}
        try:
            if action in ("ADD", "REMOVE", "EDIT"):
                creator, number = descriptionParts[1:]
                entry.update({"action": action, "creator": creator, "number": number})
            elif action == "TAGS":
                entry.update({"action": action})
            else:
                entry.update({"description": description})
        except ValueError:
            entry.update({"description": description})
        entries.append(entry)
    return entries