# -*- coding: utf-8 -*-
# Copyright 2013 Michael Helmling

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation


from os.path import join, dirname
import shutil
import tempfile
import subprocess
import hashlib

class CompilationError(Exception):
    def __init__(self, msg, log):
        Exception.__init__(self, msg)
        self.log = log

class ConversionError(Exception):
    pass

def makePreview(texcode, lang="DE", preambles=None, templateDir=None, compiler="pdflatex"):
    tmpdir = tempfile.mkdtemp()
    with open(join(tmpdir, "exercise.tex"), "wt") as f:
        f.write(texcode.encode('utf-8'))
    if preambles is None:
        preambles = []
    with open(join(tmpdir, "extra_preamble.tex"), "wt") as f:
        for line in preambles:
            f.write(line.encode('utf-8') + '\n')
    if templateDir is None:
        try:
            from exdb import repo
            templateDir = repo.templatePath()
        except:
            # use default values
            templateDir = dirname(__file__)
    template, preamble = [join(templateDir, tex) for tex in ("template.tex", "preamble.tex")]
    if lang != "DE":
        with open(template) as t:
            templateTex = t.readlines()
        templateTex[0] = templateTex[0].replace("ngerman]", "english]")
        with open(join(tmpdir, "template.tex"), "wt") as newTemplate:
            newTemplate.writelines(templateTex)
    else:
        shutil.copy(template, tmpdir) 
    shutil.copy(preamble, tmpdir)

    try:
        subprocess.check_call([compiler, "-interaction=nonstopmode", "template.tex"],
                              cwd=tmpdir)
    except subprocess.CalledProcessError as e:
        raise CompilationError(e.message, e.output)
    try:
        subprocess.check_call(["convert", "-density", "300", "template.pdf", "preview.png"],
                              cwd=tmpdir)
    except subprocess.CalledProcessError as e:
        raise ConversionError(e.message)
    return join(tmpdir, "template.pdf")