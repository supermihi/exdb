# -*- coding: utf-8 -*-
# Copyright 2013 Michael Helmling
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation

from __future__ import unicode_literals

from os.path import exists, join

from lxml import etree
from lxml.builder import E

tree = None

def initTree(tags=None):
    global tree
    import exdb
    from exdb import uni
    from exdb.repo import repoPath
    
    if tags is None:
        tags = []
    initialized = True
    if exdb.instancePath is not None:
        tagFile = join(repoPath(), "tagCategories.xml")
    else:
        initialized = False
    if initialized and exists(tagFile):
        tree = etree.parse(tagFile, encoding="utf-8").getroot()
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
    assert  tree.find("category[@name='uncategorized']") is not None 
    return tree


def storeTree():
    from exdb.repo import repoPath
    with open(join(repoPath(), "tagCategories.xml"), "wt") as f:
        f.write(etree.tostring(tree, pretty_print=True, xml_declaration=True))
            
def addTag(tag, category=('uncategorized',), position=-1):
    assert len(category) >= 1
    node = findCategory(category)
    assert len(node.xpath("./tag[text()='{}']".format(tag))) == 0
    if position == -1:
        node.append(E.tag(tag))
    else:
        node.insert(position, E.tag(tag))


def findTag(tag, category=('uncategorized',)):
    cat = findCategory(category)
    tag = cat.xpath("./tag[text()='{}']".format(tag))[0]
    return tag


def removeTag(tag, category=('uncategorized',)):
    findCategory(category).remove(findTag(tag, category))


def addCategory(name, parent=(), position=-1):
    node = findCategory(parent)
    if position == -1:
        node.append(E.category(name=name))
    else:
        node.insert(position, E.category(name=name))


def findCategory(category=('uncategorized')):
    if len(category):
        return tree.find("/".join("category[@name='{}']".format(cat) for cat in category))
    else:
        return tree


def removeCategory(category):
    assert category != ('uncategorized',)
    parent = findCategory(category[:-1])
    parent.remove(parent.find("category[@name='{}']".format(category[-1])))
    


def tags(category=('uncategorized',)):
    node = tree.find("/".join("category[@name='{}']".format(cat) for cat in category))
    return node.xpath("//text()")