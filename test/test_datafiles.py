# -*- coding: utf-8 -*-
# Copyright 2013 Michael Helmling
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation

"""Test handling of extra data files."""

import unittest

from . import makeTestRepoEnv
import exdb
from exdb import sql

class DataFilesTest(unittest.TestCase):
    
    def setUp(self):
        self.cm = makeTestRepoEnv("clone")
        self.cm.__enter__()
    
    def tearDown(self):
        self.cm.__exit__(None, None, None)
        
    def testModifications(self):
        exercise = sql.exercise("foobar", 1)
        import copy
        old = copy.copy(exercise)
        exercise.data_files.append("test.txt")
        exdb.updateExercise(exercise, {"test.txt": b""}, old)
        old = copy.copy(exercise)
        exercise.data_files = []
        self.assertRaises(exdb.tex.CompilationError, exdb.updateExercise, exercise, {}, old)