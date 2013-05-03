# -*- coding: utf-8 -*-
# Copyright 2013 Michael Helmling
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation

from nose.tools import *
from lxml import etree
def testTagTree():
    
    import exdb.tags as t
    tree = t.initTree()
    assert  tree.find("category[@name='uncategorized']") is not None
    assert  tree.find("category[@name='uncategorized']") is not None
    print("bla {}".format(tree.find("category")))
    print(etree.tostring(tree.find("category"), pretty_print=True))
    print(tree.find("category[@name='uncategorized']"))
    ok_(tree.find("category[@name='uncategorized']") is not None)
    eq_(len(list(tree)), 1)
