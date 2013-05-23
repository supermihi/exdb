exdb – A Python package for managing a database of LaTeX'ed exercises
=====================================================================

Overview
--------
[exdb][1] is a Python package for managing a database of LaTeX'ed exercises (and possibly
solutions) as used for exams or tutoral exercise sheets in universities. The goal was to
create a lightweight, robust, yet flexible package that does not require too much maintainance,
suitable for a small university working group.

The exercises are stored in a mercurial ("hg") repository. For each exercise, a data record is
serialized into an XML file with a predefined schema. That way, modifications are easy to track,
and loss of data due to accidental user behaviour or software bugs is practically made impossible.

Besides the repository, this package maintains a SQLite database that contains the same
information, but can be searched more efficiently. The database is not part of the repository and
can be rebuilt at any time from the XML files.

Being designed for exercises typeset with LaTeX, [exdb][1] also features methods to compile
exercises and generate preview images. To that end, the repository also contains template files
that define an overall TeX preamble used for all compilations, and may contain e.g. common
abbreviations or math operators.

Data model
----------
An exercise consists of a record of certain data pieces as defined by the XML schema file
`exercise.xsd` in the `exdb` folder and mapped in the class `exdb.exercise.Exercise`.
The fields are:

1. *creator*: The user name of the person who created or entered the exercise. Should be lowercase
    latin only.
2. *number*: A serial number with respect to *creator*. The pair (creator, number) serves as the
    exercise's identifier and should therefore be unique. `exdb` will find the next free number
    automatically when an exercise is added.
3. *description*: An arbitrary string (usually 1-2 sentences) describing the exercise.
4. *modified*: Time of creation or last modification.
5. *tex_preamble*: A list of single-line strings that should be added to the TeX preamble just for
    this exercise (and solution, if exists). Specific usepackages etc. should go here.
6. *tex_exercise*: A dictionary mapping two-letter uppercase language code (currently, only "DE"
    and "EN" are supported) to the corresponding LaTeX code.
7. *tex_solution*: The same as tex_exercise, but for solutions. May be left out.
8. *tags*: A list of short strings used for categorizing the exercise. Any characters except comma
   and double quote are allowed.


Tag organization
----------------
Tags are organized in tag categories: each tag belongs to at least one category. Categories can be
nested, leadinng to a layered tree structure. Note that categories are not tags themselves.
The category tree is stored in XML format inside the repository (as `tagCategories.xml`). It is a
simple XML file with the root element named `categories`, then child nodes with tag `category`
or `tag`, respectively, which have their name in a `name` attribute.


Instance Directory Layout
-------------------------
The exercise database operates on a so-called *instance directory*, which contains the repository
and some additional files and folders. The layout is as follows:

    instancepath
    |-- database.sqlite
    |-- previews
    +-- repo
         |-- .hg
         |    +-- <mercurial internals>
         |-- exercises
         |    +-- hans1
         |         |-- foo1.xml
         |         |-- exercise_EN.png
         |         +-- solution_DE.png
         |-- tagCategories.xml
         +-- templates
              |-- preamble.tex
              +-- template.tex

As you can see, the repository is located in the `repo` directory. Preview images of existing
exercises are stored alongside the XML files in `repo/exercises/<identifier>`, but NOT added
to the repository. The `previews` folder is used for temporary tex compilations.


Requirements
------------
- [Python](http://python.org) version 2.7 (with some very small changes it should also run
  under Python 3)
- [python-lxml](http://lxml.de) bindings 


Installation
------------
Simply download or check out from the [project page][1] and use directly from that directory or
install with `setup.py`, running

    python2 setup.py install
    
in the project directory.


Usage / Deployment
------------------
Before using any of `exdb`'s functionality, you must call `exdb.init(path)`, where `path` is the
instance directory. It will be created if it does not exist, leading to the basic layout as
described above.

If you have an existing repository, you should create the instance directory before calling
`exdb.init()` and checkout the repository to the `repo` subdirectory inside the instance path.

Note that `exdb`does **not** track changes to the repository made without using the `exdb`
interface. If you manually modify the repository (e.g. by pulling a new upstream version) you
therefore have to delete the `database.sql`file so that it gets properly rebuilt.   

[1]: http://github.com/supermihi/exdb