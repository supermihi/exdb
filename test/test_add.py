# -*- coding: utf-8 -*-
# Copyright 2013 Michael Helmling
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation

from __future__ import unicode_literals

from os.path import join, exists
import unittest

from . import testRepoEnv
import exdb.repo
from exdb.exercise import Exercise

class TestAddExercise(unittest.TestCase):
    
    def setUp(self):
        self.sampleExercise = Exercise(creator="helmling",
                                       description="eine Testaufgabe",
                                       tex_preamble=[r"\newcommand\bla{bla bla}"],
                                       tex_exercise={"DE" : r"\bla \bla"},
                                       tex_solution={"DE" : r"\bla geht ganz einfach.",
                                                      "EN" : r"\bla is very easy"},
                                       tags=["test", "Beispiele"])
    def test_addExercise(self):
        with testRepoEnv():
            exdb.addExercise(self.sampleExercise)
            self.assertEqual(len(exdb.exercises()), 1)
            exercise = exdb.exercises()[0]
            self.assertEqual(exercise.creator, "helmling")
            self.assertEqual(exercise.number, 1)
            self.assertTrue(exists(exdb.repo.exercisePath(exercise)))
            self.assertTrue(exists(join(exdb.repo.exercisePath(exercise), 'exercise_DE.png')))
            self.assertTrue(exists(join(exdb.repo.exercisePath(exercise), 'solution_DE.png')))
            self.assertTrue(exists(join(exdb.repo.exercisePath(exercise), 'solution_EN.png')))
            self.assertTrue(not exists(join(exdb.repo.exercisePath(exercise), 'exercise_EN.png')))