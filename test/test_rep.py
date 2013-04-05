# -*- coding: utf-8 -*-
# Copyright 2013 Michael Helmling
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation

import unittest
import exdb
from contextlib import contextmanager
from os.path import join, dirname
import shutil, tempfile

@contextmanager
def testRepoEnv():
    """Make a temporary copy of test data file *name* (without dir) and return its full path. The file
is deleted on exit."""
    origPath = join(dirname(__file__), 'data', 'testinstance')
    tempdir = tempfile.mkdtemp()
    shutil.copytree(origPath, tempdir)
    db = join(tempdir, 'test.sqlite')
    repo = join(tempdir, 'repo')
    try:
        yield repo, db
    finally:
        shutil.rmtree(tempdir)

class RepoTest(unittest.TestCase):
    
    def testAddExercise(self):
        with testRepoEnv() as (repo, db):
            exdb.init(repo, db)
            
        