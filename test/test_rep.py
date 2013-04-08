# -*- coding: utf-8 -*-
# Copyright 2013 Michael Helmling
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation

import unittest
import exdb
from . import testRepoEnv

class RepoTest(unittest.TestCase):
    
    def testAddExercise(self):
        with testRepoEnv():
            pass
            
        