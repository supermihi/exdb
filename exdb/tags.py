# -*- coding: utf-8 -*-
# Copyright 2013 Michael Helmling
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation

from __future__ import unicode_literals, print_function

from os.path import exists, join
import json
from collections import OrderedDict
from itertools import izip_longest

from lxml import etree
from lxml.builder import E

def initTagsTable(conn):
    """Initialize the *tags* table in the SQLite database from the tagCategories.xml file.
    
    If the file does not exist, a barebone tree containing only the "uncategorized"
    category is created and used instead. Returns the root of the XML tree.
    """
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tags;")
    import exdb
    from exdb.repo import repoPath

    initialized = False
    if exdb.instancePath is not None:
        tagFile = join(repoPath(), "tagCategories.xml")
        initialized = True
    tree = etree.parse(tagFile).getroot() if initialized and exists(tagFile) else initialTree()
    uncat = tree.find("category[@name='uncategorized']") 
    if uncat is None:
        uncat = E.category(name='uncategorized')
        tree.append(uncat)        
    for node in tree.iterdescendants():
        parents = list(reversed([el.get("id") for el in node.iterancestors()][:-1]))
        matpath = '.'.join(map(str, parents)) + '.'
        if matpath[0] != '.':
            matpath = "." + matpath
        cursor.execute("INSERT INTO tags(name, is_tag, parent, mat_path) VALUES (?, ?, ?, ?)",
                     (node.get("name"), node.tag == "tag",
                      parents[-1] if len(parents) else None, matpath))
        node.set("id", str(cursor.lastrowid))
        node.set("matpath", matpath)
    conn.commit()
    return tree

def initialTree():
    return E.categories(E.category(name='uncategorized'))

def readTreeFromTable(conn):
    """Parse the *tags* SQLite table into an LXML tree and return its root."""
    root = E.categories()
    for row in conn.execute("SELECT id, name, is_tag, mat_path FROM tags ORDER BY id ASC"):
        parents = row[3][1:-1].split(".")
        if len(parents) > 0 and len(parents[0]) > 0:
            parent = root.xpath("/".join("category[@id='{}']".format(cat) for cat in parents))[0]
        else:
            parent = root
        element = etree.Element("tag" if row[2] else "category", id=str(row[0]), name=row[1],
                                mat_path=row[3])
        parent.append(element)
    return root

def compareTrees(tree1, tree2):
    for pre, post in izip_longest(tree1.iter(), tree2.iter(), fillvalue=None):
        if pre is None or post is None:
            return False
        if pre.tag != post.tag:
            return False
        if pre.attrib != post.attrib:
            return False
        if len(pre) != len(post):
            return False
    return True

class JSONTreeEncoder(json.JSONEncoder):
    """A specialized JSON encoder to encode the tag XML tree into JSON suitable for dynatree.
    
    Converts the XML tree into a list of toplevel categories. Categories and tags are encoded
    to JSON objects with "title" set to their name, the XML tag is either "tag" or "category",
    the database id (if exists) is stored in the attribute "id", and the materialized path
    (if known) in "mat_path". Children are put as a list in the "children" attribute.
    """
    def default(self, obj):
        if isinstance(obj, etree._Element):
            if obj.tag == "categories":
                return obj.getchildren()
            dct = OrderedDict(title=obj.get("name"), id=obj.get("id"), is_tag=obj.tag=="tag",
                              mat_path=obj.get("mat_path"))
            if obj.tag == "category":
                dct["isFolder"] = True
                dct["expand"] = True
                dct["children"] = obj.getchildren()
                if obj.get("mat_path") == "." and obj.get("name") == "uncategorized":
                    dct["locked"] = True
                    dct["activate"] = True
            return dct
        return json.JSONEncoder.default(self, obj)


def toJSON(tree):
    """Convert the given XML tree to a JSON string, using the above encoder.""" 
    return JSONTreeEncoder().encode(tree)


def lxmlObjectHook(dct):
    """Object hook for parsing JSON back to XML."""
    tag = "tag" if dct['is_tag'] else "category"
    elem = etree.Element(tag, name=dct['title'])
    if dct.get("id"):
        elem.set("id", str(dct["id"]))
    if dct.get("mat_path"):
        elem.set("mat_path", dct["mat_path"])
    if tag == "category" and "children" in dct:
        elem.extend(dct["children"])
    return elem


def fromJSON(js):
    """Parse the given json string *js* to an LXML tree; returns the root "categories" element."""
    return E.categories(*json.loads(js, object_hook=lxmlObjectHook))


def storeTree(tree):
    """Store the XML *tree* to the appropriate tagCategories.xml file.""" 
    from exdb.repo import repoPath
    from copy import deepcopy
    tree = deepcopy(tree)
    for element in tree.iter():
        try:
            del element.attrib["id"]
        except KeyError:
            pass
        try:
            del element.attrib["mat_path"]
        except KeyError:
            pass
    with open(join(repoPath(), "tagCategories.xml"), "wt") as f:
        f.write(etree.tostring(tree, pretty_print=True, xml_declaration=True))