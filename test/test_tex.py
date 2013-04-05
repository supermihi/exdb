# -*- coding: utf-8 -*-
# Copyright 2013 Michael Helmling
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation

from exdb.tex import makePreview
import unittest

class TestCompilation(unittest.TestCase):
    
    def setUp(self):
        self.tex_de = ur"öhm \silly \"ohm \dots ein Integral: $\int_\R^b \mathrm{d}x$ "
        self.tex_en = "bla bla $x^2$"
        self.preambles = [r"\newcommand\silly{SILLY}"]
        
    def test_pdflatex(self):
        makePreview(self.tex_de, lang="DE", compiler="pdflatex", preambles=self.preambles)
        makePreview(self.tex_en, lang="EN", compiler="pdflatex", preambles=self.preambles)
    
    def test_xelatex(self):
        makePreview(self.tex_de, lang="DE", compiler="xelatex", preambles=self.preambles)
        makePreview(self.tex_en, lang="EN", compiler="xelatex", preambles=self.preambles)
        
    def test_lualatex(self):
        makePreview(self.tex_de, lang="DE", compiler="lualatex", preambles=self.preambles)
        makePreview(self.tex_en, lang="EN", compiler="lualatex", preambles=self.preambles)