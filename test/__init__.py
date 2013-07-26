# -*- coding: utf-8 -*-
# Copyright 2013 Michael Helmling
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation

from os.path import join, dirname
import tempfile
import shutil
from contextlib import contextmanager

def dataPath(path):
    """Return the absoulte path of *path* which is relative to the test data directory."""
    return join(dirname(__file__), "data", path)

@contextmanager
def makeTestRepoEnv(mode, **kwargs):
    """Creates a temporary instance and calls exdb.init() on that instance's path.
    
    *mode* is one of:
      - "empty" (creates an empty instance),
      - "clone" (clones the test instance from the data directory)
      - "copy" (copies the test instance from the data directory)

    Additional args are passed to the init function.
    After exiting the context manager, the instance is deleted and the previous
    exdb.instancePath is restored.
    """
    import exdb
    oldInstancePath = exdb.instancePath
    tmpdir = tempfile.mkdtemp()
    if mode == "empty":
        exdb.init(tmpdir, **kwargs)
    elif mode == "clone":
        # copy the source so that pushes don't change the test data
        reposrc = join(tmpdir, "hgsrc")
        shutil.copytree(dataPath("testinstance/repo"), reposrc)
        exdb.init(join(tmpdir, "instance"), repository=reposrc, **kwargs)
    else:
        assert mode == "copy"
        instanceDir = join(tmpdir, "instance")
        shutil.copytree(dataPath("testinstance"), instanceDir)
        exdb.init(instanceDir, **kwargs)
    try:
        yield
    finally:
        exdb.init(oldInstancePath)
        shutil.rmtree(tmpdir)
        
