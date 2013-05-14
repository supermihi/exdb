# -*- coding: utf-8 -*-
# Copyright 2013 Michael Helmling
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation

from nose.tools import assert_equal, assert_is_not_none, assert_true, assert_raises
import unittest
from exdb import tags
from lxml import etree
from . import dataPath


def testJSONEncodeDecode():
    
    tree = etree.parse(dataPath("tagCategories.xml")).getroot()
    js = tags.toJSON(tree)
    back = tags.fromJSON(js)
    for pre, post in zip(tree.iter(), back.iter()):
        assert_equal(pre.tag, post.tag)
        assert_equal(pre.attrib, post.attrib)
    assert_true(tags.compareTrees(tree, back))
    
