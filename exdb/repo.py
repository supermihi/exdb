# -*- coding: utf-8 -*-
# Copyright 2013 Michael Helmling
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation

from __future__ import unicode_literals

import io, os, subprocess, shutil
from os.path import basename, dirname, join, exists, relpath


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

def xmlPath(*args, **kwargs):
    """Return the path of the exercise's XML file. Takes the same arguments as *exercisePath*.
    """
    exerciseDir = exercisePath(*args, **kwargs)
    return join(exerciseDir, basename(exerciseDir) + ".xml")


def callHg(*args, **kwargs):
    """Calls the hg script in the repo directory with given args.
    
    Any keyword arguments are passed to the subprocess.check_output function call.
    """
    if "cwd" not in kwargs:
        kwargs["cwd"] = repoPath()
    return subprocess.check_output(["hg"] + list(args), **kwargs)


def initRepository(source=None):
    """Ensure that an initial exercise repository exists.
    
    If the "repo" directory already exists, nothing happens. Otherwise, if *source* is given,
    the repository is cloned from that URI; if not, an initial repository is created with the
    default templates provided by this package.
    """
    path = repoPath()
    if not exists(path):
        os.makedirs(path)
    hgChanges = False
    if not exists(join(path, ".hg")):
        if source:
            callHg("clone", source, path)
        else:
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


def loadFiles(creator, number, filenames):
    """Load image files with names *filenames* for the specified exercise.
    
    Returns a list of (filename, data) tuples.
    """
    exPath = exercisePath(creator=creator, number=number)
    files = {}
    for name in filenames:
        data = open(join(exPath, name), "rb").read()
        files[name] = data
    return files
    
    
def storeExerciseXML(exercise):
    """Write the XML file encoding the given exercise to the appropriate path."""
    with io.open(xmlPath(exercise=exercise), "wt", encoding="utf-8") as f:
        f.write(exercise.toXML())


def loadFromXML(creator, number):
    from exdb.exercise import Exercise
    return Exercise.fromXMLFile(xmlPath(creator=creator, number=number))


def compileSnippets(exercise, files, old=None, copy=False, init=False):
    """Compiles all TeX snippets of *exercise* or raises an error if this is not possible.
    
    *files* is a dict mapping filename to data of newly uploaded files.
    
    If *copy* is True, successfully compiled previews are copied into the exercise directory in the
    repository, i.e., become the "official" previews.
    If the exercise existed before, it should be given in *old*. This function will only recompile
    parts that have potentially changed against the old version.
    
    Returns a dictionary mapping (textype,lang) tuples to (previewtype, path) tuples, where
    *previewtype* is one of "preview" and "temp" and *path* is the absolute image path.
    
    *init* enables a special mode made for initializing the repository after e.g. cloning. It
    generates all previews which do not yet exist in the filesystem (implies *copy=True*).
    
    If compilation of a snippet fails, a tex.CompilationError exception is raised. Besides its
    normal attribute, the *successful* attribute contains the dictionary that would normally be
    returned (containing links to all snippets compiled successfully so far), and the *textype*
    and *lang* attributes of the exception tell which snippet failed.
    """
    if old:
        old = loadFromXML(exercise.creator, exercise.number)
        files = files.copy()
        files.update(loadFiles(exercise.creator, exercise.number,
                               (n for n in exercise.data_files if n not in files)))
        compileAll = False
        if len(files) > 0:
            compileAll = True
        elif old.tex_preamble != exercise.tex_preamble:
            compileAll = True
        elif old.data_files != exercise.data_files:
            compileAll = True
    else:
        compileAll = True
    if init:
        copy=True
        files = loadFiles(exercise.creator, exercise.number, exercise.data_files)
    from . import tex
    ret = {}
    for textype in "exercise", "solution":
        dct = exercise["tex_" + textype]
        for lang, code in dct.items():
            try:
                target = join(exercisePath(exercise), "{}_{}.png".format(textype, lang))
                if init and exists(target):
                    continue
                if not compileAll and old:
                    try:
                        if old["tex_"+textype][lang] == code:
                            ret[textype, lang] = ("preview", target)
                            continue
                    except KeyError:
                        pass
                imgpath = tex.makePreview(code, lang, exercise.tex_preamble, files)
                ret[textype, lang] = ("temp", imgpath)
                if copy:
                    shutil.copy(imgpath, target)
                    shutil.rmtree(dirname(imgpath))
            except tex.CompilationError as e:
                e.textype = textype
                e.lang = lang
                e.successful = ret
                raise e
    return ret


def addExercise(exercise, files):
    """Adds the given exercise to the repository.
    
    *files* is a dict mapping filenames to data for all external data files.
    """
    basePath = exercisePath(exercise)
    os.mkdir(basePath)
    xmlPath = join(basePath, exercise.identifier() + ".xml")
    with io.open(xmlPath, "wt", encoding="utf-8") as f:
        f.write(exercise.toXML())
    callHg("add", relpath(xmlPath, repoPath()))
    for fname, fdata in files.items():
        fPath = join(basePath, fname)
        with open(fPath, "wb") as f:
            f.write(fdata)
        callHg("add", relpath(fPath, repoPath()))            
    commitMessage = "ADD {} {}".format(exercise.creator, exercise.number)
    callHg("commit", "-u", exercise.creator, "-m", commitMessage)
    pushIfRemote()
    compileSnippets(exercise, files, copy=True)


def updateExercise(exercise, files, old, user=None):
    """Updates the given exercise on disk and in the repository.
    
    This method writes the XML file and possible data files, generates previews, and commits
    the repository.
    """
    basePath = exercisePath(exercise)
    # delete removed data files from the repository
    for removedFile in set(old.data_files) - set(exercise.data_files):
        callHg("remove", relpath(join(basePath, removedFile), repoPath()))
    # delete previews of removed tex snippets
    for textype in "exercise", "solution":
        dct = old["tex_"+textype]
        for lang in dct:
            if lang not in exercise["tex_"+textype]:
                os.remove(join(basePath, "{}_{}.png".format(textype, lang)))
    # add newly uploaded files
    for fname, fdata in files.items():
        fPath = join(basePath, fname)
        with open(fPath, "wb") as f:
            f.write(fdata)
        if fname not in old.data_files: # otherwise an existing data file was replaced
            callHg("add", relpath(fPath, repoPath()))
    storeExerciseXML(exercise)
    commitMessage = "EDIT {} {}".format(exercise.creator, exercise.number)
    callHg("commit", "-u", user or exercise.creator, "-m", commitMessage)
    pushIfRemote()
    compileSnippets(exercise, files, old, copy=True)


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
