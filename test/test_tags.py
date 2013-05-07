# -*- coding: utf-8 -*-
# Copyright 2013 Michael Helmling
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation

from nose.tools import assert_equal, assert_is_not_none, assert_true, assert_raises

from lxml import etree
def testTagTree():
    
    import exdb.tags as t
    tree = t.initTree()
    assert  tree.find("category[@name='uncategorized']") is not None
    assert  tree.find("category[@name='uncategorized']") is not None
    assert_true(tree.find("category[@name='uncategorized']") is not None)
    assert_equal(len(list(tree)), 1)
    
    t.addTag('sundekalm')
    assert_raises(AssertionError, t.addTag, 'sundekalm')
    t.addTag('blub')
    assert_equal(t.tags(), ['sundekalm', 'blub'])
    t.addTag('between', position=1)
    assert_equal(t.tags(), ['sundekalm', 'between', 'blub'])
    t.removeTag('between')
    assert_equal(t.tags(), ['sundekalm', 'blub'])
    
    t.addCategory("test")
    t.addCategory("subtest", ("test",))
    assert_is_not_none(t.findCategory(("test", "subtest")))
    t.addTag("subtesttag", ("test", "subtest"))
    t.removeCategory(("test", "subtest"))
    assert_raises(AttributeError, t.findTag, "subtesttag", ("test", "subtest"))
    
