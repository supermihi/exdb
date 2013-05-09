# -*- coding: utf-8 -*-
# Copyright 2013 Michael Helmling
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation

from __future__ import unicode_literals, print_function

from os.path import exists, join

from lxml import etree
from lxml.builder import E

def initTagsTable(conn):
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tags;")
    import exdb
    from exdb.repo import repoPath
    
    initialized = False
    if exdb.instancePath is not None:
        tagFile = join(repoPath(), "tagCategories.xml")
        initialized = True
    if initialized and exists(tagFile):
        tree = etree.parse(tagFile).getroot()
    else:
        tree = initialTree()
    uncat = tree.find("category[@name='uncategorized']") 
    if uncat is None:
        uncat = E.category(name='uncategorized')
        tree.append(uncat)
        
    for node in tree.iterdescendants():
        parents = list(reversed([el.get("id") for el in node.iterancestors()][:-1]))
        matpath = '.'.join(map(str, parents)) + '.'
        cursor.execute("INSERT INTO tags(name, type, parent, mat_path) VALUES (?, ?, ?, ?)",
                     (node.get("name"), node.tag, parents[-1] if len(parents) else None, matpath))
        
        node.set("id", str(cursor.lastrowid))
    print(etree.tostring(tree, pretty_print=True))
    conn.commit()
    return tree

def initialTree():
    return E.categories( E.category(name='uncategorized') )

def readTreeFromTable(conn):
    root = E.categories()
    for row in conn.execute("SELECT id, name, type, mat_path FROM tags ORDER BY id ASC"):
        parents = row[3][:-1].split(".")
        if len(parents) > 0 and len(parents[0]) > 0:
            parent = root.xpath("/".join("category[@id='{}']".format(cat) for cat in parents))
        else:
            parent = root
        element = etree.Element(row[2], id=str(row[0]), name=row[1])
        parent.append(element)
    return root

def storeTree(tree):
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