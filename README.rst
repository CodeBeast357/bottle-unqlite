=====================
Bottle-UnQLite
=====================

.. image:: https://travis-ci.org/CodeBeast357/bottle-unqlite.svg?branch=master
    :target: https://travis-ci.org/CodeBeast357/bottle-unqlite
    :alt: Build Status - Travis CI

UnQLite is a self-contained NoSQL database engine that runs locally and does not 
require any additional server software or setup.

This plugin simplifies the use of unqlite databases in your Bottle applications. 
Once installed, all you have to do is to add a ``db`` keyword argument 
(configurable) to route callbacks that need a database connection.

Installation
===============

Install with one of the following commands::

    $ pip install bottle-unqlite
    $ easy_install bottle-unqlite

or download the latest version from github::

    $ git clone git://github.com/CodeBeast357/bottle-unqlite.git
    $ cd bottle-unqlite
    $ python setup.py install

Usage
===============

Once installed to an application, the plugin passes an open 
:class:`unqlite.UnQLite` instance to all routes that require a ``db`` keyword 
argument::

    import bottle

    app = bottle.Bottle()
    plugin = bottle.ext.unqlite.Plugin(filename='/tmp/test.db')
    app.install(plugin)

    @app.route('/show/:item')
    def show(item, db):
        itemset = db.collection('items').filter(lambda x: x['name'] == item)
        if itemset:
            return template('showitem', page=itemset[0])
        return HTTPError(404, "Page not found")

Routes that do not expect a ``db`` keyword argument are not affected.

At the end of the request cycle, outstanding transactions are committed and the 
connection is closed automatically. If an error occurs, any changes to the database 
since the last commit are rolled back to keep the database in a consistent state.

Configuration
=============

The following configuration options exist for the plugin class:

* **filename**: Database filename (default: in-memory database, ``':mem:'``).
* **keyword**: The keyword argument name that triggers the plugin (default: ``'db'``).
* **flags**: How to open the database (default: open or create database, ``UnQLite.UNQLITE_OPEN_CREATE``).
* **open_database**: Whether or not to open the connection on initialization (default: ``True``).

You can override each of these values on a per-route basis:: 

    @app.route('/cache/:item', unqlite={'filename': ':mem:'})
    def cache(item, db):
        ...
   
or install two plugins with different ``keyword`` settings to the same application::

    app = bottle.Bottle()
    test_db = bottle.ext.unqlite.Plugin(filename='/tmp/test.db')
    cache_db = bottle.ext.unqlite.Plugin(filename=':mem:', keyword='cache')
    app.install(test_db)
    app.install(cache_db)

    @app.route('/show/:item')
    def show(item, db):
        ...

    @app.route('/cache/:item')
    def cache(item, cache):
        ...
