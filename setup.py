#!/usr/bin/python2
# -*- coding: utf-8 -*-
# Copyright 2013 Michael Helmling
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation

from setuptools import setup, find_packages
import os, io

def readme():
    readmeFile = os.path.join(os.path.dirname(__file__), 'README.md')
    return io.open(readmeFile, "r", encoding="utf-8").read()

setup(name='exdb',
      version='0.2',
      description="a Python package for managing a database of LaTeX'ed exercises",
      long_description=readme(),
      author='Michael Helmling',
      author_email='michaelhelmling@posteo.de',
      url='http://github.com/supermihi/exdb',
      license='GPL3',
      packages=find_packages(),
      include_package_data=True,
      install_requires=["lxml", "mercurial"],
      test_requires=["nose"],
      test_suite="nose.collector"
    )
