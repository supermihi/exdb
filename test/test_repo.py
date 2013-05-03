# -*- coding: utf-8 -*-
# Copyright 2013 Michael Helmling
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation

from __future__ import unicode_literals, print_function

import unittest
import exdb
from exdb.exercise import Exercise
import tempfile
from os.path import join
from . import dataPath
import shutil

tmpDir = None
instanceDir = None

def setUpModule():
    global tmpDir, instanceDir
    tmpDir = tempfile.mkdtemp()
    instanceDir = join(tmpDir, "instance")
    shutil.copytree(dataPath("testinstance"), instanceDir)
    exdb.init(instanceDir)


def tearDownModule():
    shutil.rmtree(tmpDir)
    exdb.instancePath = None
    
class TestRepository(unittest.TestCase):


    def testRepository(self):
        self.assertEqual(len(exdb.sql.exercises()), 1)
        theEx = exdb.sql.exercises()[0]
        self.assertEqual(theEx.creator, "jensmander")
        self.assertEqual(theEx.number, 1)
        
        exercise = Exercise.fromXMLFile(dataPath("jemand1.xml"))
        exercise.number = None
        exdb.addExercise(exercise)
        self.assertEqual(exercise.number, 1)
        self.assertEqual(len(exdb.sql.exercises()), 2)
        exdb.removeExercise("jensmander", 1)
        self.assertEqual(len(exdb.sql.exercises()), 1)
        theEx = exdb.sql.exercises()[0]
        self.assertEqual(theEx.creator, "jemand")
        history = exdb.repo.history()
        self.assertEqual(history[0]["author"], "jensmander")
        self.assertEqual(history[0]["action"], "REMOVE")
        self.assertEqual(history[1]["action"], "ADD")
            
        