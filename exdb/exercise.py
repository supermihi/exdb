# -*- coding: utf-8 -*-
# Copyright 2013 Michael Helmling
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation

from lxml import etree
from lxml.builder import E

import datetime
from os.path import join, dirname

class VersionMismatchError(Exception):
    def __init__(self, ours, yours):
        Exception.__init__(self, "Schema version {} is too recent (expected <= {})".format(yours, ours))

class Exercise:
    
    DATEFMT = "%Y-%m-%dT%H:%M:%S"
    parser = None
    
    attributes = ["number", "creator", "description", "modified", "tex_preamble", "tex_exercise", "tex_solution", "tags"]
    def __init__(self, **kwargs):
        self.tex_exercise = {}
        self.tex_solution = {}
        self.tex_preamble = []
        self.tags = []
        self.description = ""
        self.number = None
        self.modified = datetime.datetime.now()
        for key, value in kwargs.items():
            if key in Exercise.attributes:
                setattr(self, key, value)
            else:
                raise ValueError("Unknown keyword arg '{}' for Exercise".format(key))
    
    def identifier(self):
        return "{}{}".format(self.creator, self.number)
    
    def toXML(self):
        Exercise.initXSD()
        xml = (
            E.exercise(
                E.creator(self.creator),
                E.number(str(self.number)),
                E.description(self.description),
                E.modified(self.modified.strftime(self.DATEFMT)),
                schemaversion=str(Exercise.SCHEMAVERSION)
            )
        )
        xml.set("{http://www.w3.org/2001/XMLSchema-instance}noNamespaceSchemaLocation", "exercise.xsd")
        for line in self.tex_preamble:
            xml.append(E.tex_preamble(line))
        for lang, text in self.tex_exercise.items():
            xml.append(E.tex_exercise(text, lang=lang))
        for lang, text in self.tex_solution.items():
            xml.append(E.tex_solution(text, lang=lang))
        for tag in self.tags:
            xml.append(E.tag(tag))                
        return etree.tostring(xml, encoding="utf-8", xml_declaration=True, pretty_print=True)
        
    
    @staticmethod
    def initXSD():
        if Exercise.parser is None:
            xsd = etree.parse(join(dirname(__file__), "exercise.xsd"))
            Exercise.SCHEMAVERSION = int(xsd.getroot().get("version"))
            schema = etree.XMLSchema(xsd)
            Exercise.parser = etree.XMLParser(schema=schema)

    @staticmethod
    def fromXMLString(data):
        Exercise.initXSD()
        parser = Exercise.parser
        root = etree.fromstring(data, parser)
        exercise = Exercise()
        exercise.schemaversion = int(root.get('schemaversion'))
        if exercise.schemaversion > Exercise.SCHEMAVERSION:
            raise VersionMismatchError(Exercise.SCHEMAVERSION, exercise.schemaversion)
        exercise.creator = root.findtext('creator')
        exercise.number = int(root.findtext('number'))
        exercise.description = root.findtext('description')
        exercise.modified = datetime.datetime.strptime(root.findtext('modified'), Exercise.DATEFMT)
        for elem in root.findall('tex_preamble'):
            exercise.tex_preamble.append(elem.text)
        for extex in root.findall('tex_exercise'):
            exercise.tex_exercise[extex.get('lang')] = extex.text
        for soltex in root.findall('tex_solution'):
            exercise.tex_solution[soltex.get('lang')] = soltex.text
        for tag in root.findall('tag'):
            exercise.tags.append(tag.text)
        return exercise
    
    def __str__(self):
        return "Exercise(" + ", ".join("{}={}".format(attr,getattr(self, attr)) for attr in self.attributes) + ")"
    
    __repr__ = __str__