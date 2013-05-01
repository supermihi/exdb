# -*- coding: utf-8 -*-
# Copyright 2013 Michael Helmling
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation

from os.path import exists, join

from lxml import etree
from lxml.builder import E

tree = None

def initTree(tags=None):
    global tree
    import exdb
    from exdb import uni
    tagFile = join(exdb.instancePath, "tagCategories.xml")
    if exists(tagFile):
        tree = etree.parse(tree, encoding="utf-8").getroot()
    else:
        tree = E.categories()
    uncat = tree.find("category[@name='uncategorized']") 
    if uncat is None:
        uncat = E.category(name='uncategorized')
        tree.append(uncat)
    existingTags = set(uni(elem.text) for elem in tree.findall('tag'))
    for tag in tags:
        if tag not in existingTags:
            uncat.append(E.tag(tag))
    print(etree.tostring(tree, pretty_print=True))
    return tree