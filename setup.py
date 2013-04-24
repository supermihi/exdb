#!/usr/bin/python2
# -*- coding: utf-8 -*-
# Copyright 2013 Michael Helmling
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation

from setuptools import setup, find_packages

setup(name='exdb',
      version='0.1-git',
      description='python package to manage a database of exercises within a mercurial repository',
      author='Michael Helmling',
      author_email='michaelhelmling@posteo.de',
      url='http://github.com/supermihi/exdb',
      license='GPL3',
      packages=find_packages(),
      include_package_data=True,
      install_requires=["lxml"],
      test_suite="test"
    )