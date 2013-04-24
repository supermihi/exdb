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

@contextmanager
def testRepoEnv():
    """Creates a temporary instance and calls exdb.init() on that instance's path.
    
    Afterwards, the instance is deleted and the previous exdb.instancePath is restored.
    """
    import exdb
    oldInstancePath = exdb.instancePath
    instancePath = tempfile.mkdtemp()
    exdb.init(instancePath)
    try:
        yield
    finally:
        exdb.init(oldInstancePath)
        shutil.rmtree(instancePath)
        
