# -*- coding: utf-8 -*-
# Copyright 2013 Michael Helmling

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation

from __future__ import unicode_literals

import io, os, shutil, subprocess, tempfile
from os.path import join, dirname
import hashlib


class CompilationError(Exception):
    """Error indicating that LaTeX compilation has failed."""
    def __init__(self, msg, log):
        self.msg = msg
        self.log = log
        
    def __str__(self):
        return b"{}\n{}".format(self.msg, self.log)


class ConversionError(Exception):
    """This error indicates that the pdf->png conversion has failed."""
    pass


def makePreview(texcode, lang="DE", preambles=None, compiler="pdflatex"):
    """Create a preview image for the given tex code.

    If exdb is initialized with an instance dir, the preview is generated inside the preview
    directory in a subdirectory determined by the SHA256 sum of the parameters. Thus, this can
    quickly return a previously computed preview for the same data.
    
    If the compilation succeeds, the absolute path of the preview image is returned. The caller
    should remove its parent directory (containing all tex output files) as soon as it is not
    needed anymore.
    
    Otherwise, a CompilationError is raised, containing the TeX log in its *log* attribute. If 
    conversion to png fails, a ConversionError is raised. In both error cases, the compile
    directory is deleted before raising the exception.
    """
    if preambles is None:
        preambles = []
    # create directory for the files
    import exdb
    if exdb.instancePath:
        previewPath = join(exdb.instancePath, "previews")
        h = hashlib.sha256()
        for line in preambles:
            h.update(line.encode('utf-8'))
        h.update(lang.encode('utf-8'))
        h.update(compiler.encode('utf-8'))
        h.update(texcode.encode('utf-8'))
        tmpdir = join(previewPath, h.hexdigest())
        if os.path.exists(tmpdir):
            image = os.path.join(tmpdir, "preview.png")
            if os.path.exists(image):
                return image
        else:
            os.mkdir(tmpdir)
    else:
        tmpdir = tempfile.mkdtemp()
    # write *texcode* to exercise.tex
    with io.open(join(tmpdir, "exercise.tex"), "wt", encoding='utf-8') as f:
        f.write(texcode)
    # create extra_preambles.tex from *preambles*
    with io.open(join(tmpdir, "extra_preamble.tex"), "wt", encoding='utf-8') as f:
        for line in preambles:
            f.write(line + '\n')
    # compute templateDir
    try:
        from exdb import repo
        templateDir = repo.templatePath()
    except:
        templateDir = dirname(__file__)
    template, preamble = [join(templateDir, tex) for tex in ("template.tex", "preamble.tex")]
    # replace language in the template if it's not german
    if lang != "DE":
        with open(template) as t:
            templateTex = t.readlines()
        templateTex[0] = templateTex[0].replace("ngerman]", "english]")
        with open(join(tmpdir, "template.tex"), "wt") as newTemplate:
            newTemplate.writelines(templateTex)
    else:
        shutil.copy(template, tmpdir) 
    shutil.copy(preamble, tmpdir)

    # call the compiler
    try:
        subprocess.check_output([compiler,
                                 "-interaction=nonstopmode",
                                 "-no-shell-escape",
                                 "-file-line-error",
                                 "template.tex"],
                                 cwd=tmpdir, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        shutil.rmtree(tmpdir)
        raise CompilationError(str(e), e.output)
    try:
        subprocess.check_call(["convert", "-density", "200", "template.pdf", "preview.png"],
                              cwd=tmpdir)
    except subprocess.CalledProcessError as e:
        shutil.rmtree(tmpdir)
        raise ConversionError(e.message)
    return join(tmpdir, "preview.png")