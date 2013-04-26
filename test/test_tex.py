# -*- coding: utf-8 -*-
# Copyright 2013 Michael Helmling
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation

from __future__ import unicode_literals

from exdb.tex import makePreview, CompilationError
from . import testRepoEnv
import os.path, shutil
import unittest

class TestCompilation(unittest.TestCase):
    
    def setUp(self):
        self.tex_de = r"öhm \silly \"ohm \dots ein Integral: $\int_\R^b \mathrm{d}x$ "
        self.tex_en = "bla bla $x^2$"
        self.tex_invalid = "bla bla $open math"
        self.preambles = [r"\newcommand\silly{SILLY}"]
    
    def runPreview(self, *args, **kwargs):
        image = makePreview(*args, preambles=self.preambles, **kwargs)
        self.assertTrue(os.path.exists(image))
        shutil.rmtree(os.path.dirname(image))
        
    def test_pdflatex(self):
        self.runPreview(self.tex_de, compiler="pdflatex")
        self.runPreview(self.tex_en, compiler="pdflatex", lang="EN")
        self.assertRaisesRegexp(CompilationError, r"Missing \$ inserted",
                                lambda : self.runPreview(self.tex_invalid, compiler="pdflatex"))
    
    def test_xelatex(self):
        self.runPreview(self.tex_de, compiler="xelatex")
        self.runPreview(self.tex_en, compiler="xelatex", lang="EN")
        self.assertRaisesRegexp(CompilationError, r"Missing \$ inserted",
                                lambda : self.runPreview(self.tex_invalid, compiler="xelatex"))
        
    def test_lualatex(self):
        self.runPreview(self.tex_de, compiler="lualatex")
        self.runPreview(self.tex_en, compiler="lualatex", lang="EN")
        self.assertRaisesRegexp(CompilationError, r"Missing \$ inserted",
                                lambda : self.runPreview(self.tex_invalid, compiler="lualatex"))
    
    def test_previewPath(self):
        with testRepoEnv():
            image = makePreview(self.tex_de, preambles=self.preambles, compiler="pdflatex")
            import exdb.tex
            self.assertTrue(os.path.exists(image))
            self.assertTrue(image.startswith(exdb.tex.previewPath()))