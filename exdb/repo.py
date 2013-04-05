# -*- coding: utf-8 -*-
# Copyright 2013 Michael Helmling
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation

from os.path import join, exists
import os
import subprocess, shutil

repoPath = None
def callHg(*args, **kwargs):
    if "cwd" not in kwargs:
        kwargs["cwd"] = repoPath
    return subprocess.check_call(["hg"] + args, **kwargs)

def templatePath():
    if repoPath is None:
        raise Exception("exdb.repo is not initialized")
    return join(repoPath, "templates")

def initRepository(path, overwrite=False):
    """Creates an initial hg repository at the given *path*.
    
    If *overwrite* is True and the path exists, it will be removed without warning.
    """
    
    global repoPath
    repoPath = path
    if exists(path):
        if overwrite:
            shutil.rmtree(path)
    os.makedirs(path)
    callHg("init")
    for subdir in ("templates", "exercises"):
        os.mkdir(join(path, subdir))
        callHg("add", subdir)
