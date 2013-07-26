# -*- coding: utf-8 -*-
# Copyright 2013 Michael Helmling
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation

from __future__ import unicode_literals, print_function

import unittest
import tempfile
import os
from os.path import exists, join
import shutil, glob

from . import dataPath, makeTestRepoEnv
from exdb.repo import repoPath
import exdb
from exdb.exercise import Exercise
    
class TestRepository(unittest.TestCase):
    
    def setUp(self):
        self.cm = makeTestRepoEnv("copy")
        self.cm.__enter__()
    
    def tearDown(self):
        self.cm.__exit__(None, None, None)
    
    def testRepositoryOperations(self):
        """Adds and removes exercises and checks the history."""
        numExercises = len(glob.glob(join(exdb.repo.repoPath(), "exercises", "*", "*.xml" )))
        self.assertEqual(len(exdb.sql.exercises()), numExercises)
        exes = exdb.sql.exercises()
        self.assertEqual(set(ex.creator for ex in exes), set(("jensmander", "foobar")))
        self.assertTrue(all(ex.number == 1 for ex in exes))
        
        exercise = Exercise.fromXMLFile(dataPath("jemand1.xml"))
        exercise.number = None
        exdb.addExercise(exercise, {})
        self.assertEqual(exercise.number, 1)
        self.assertEqual(len(exdb.sql.exercises()), numExercises+1)
        exdb.removeExercise("jensmander", 1)
        self.assertEqual(len(exdb.sql.exercises()), numExercises)
        exes = exdb.sql.exercises()
        self.assertNotIn("jensmander", (ex.creator for ex in exes))
        history = exdb.repo.history()
        self.assertEqual(history[0]["author"], "jensmander")
        self.assertEqual(history[0]["action"], "REMOVE")
        self.assertEqual(history[1]["action"], "ADD")


class TestCloneInit(unittest.TestCase):
    """Initializes an instance by cloning a HG repository."""
    
    def testInitFromUrl(self):
        """Checks that XML and data files are present and previews generated."""
        with makeTestRepoEnv("clone"):
            self.assertTrue(exists(join(repoPath(), "tagCategories.xml")))
            for filename in ("foobar1.xml", "example.cpp", "solution_EN.png",
                             "solution_DE.png", "exercise_DE.png"):
                self.assertTrue(exists(join(repoPath(), "exercises", "foobar1", filename)), "{} missing".format(filename))
