# -*- coding: utf-8 -*-
'''
Bottle-unqlite is a plugin that integrates UnQLite with your Bottle
application. It automatically connects to a database at the beginning of a
request, passes the database handle to the route callback and closes the
connection afterwards.

To automatically detect routes that need a database connection, the plugin
searches for route callbacks that require a `db` keyword argument
(configurable) and skips routes that do not. This removes any overhead for
routes that don't need a database connection.

Usage Example::

    import bottle
    from bottle.ext import unqlite

    app = bottle.Bottle()
    plugin = unqlite.Plugin(filename='/tmp/test.db')
    app.install(plugin)

    @app.route('/show/:item')
    def show(item, db):
        itemset = db.collection('items').filter(lambda x: x['name'] == item)
        if itemset:
            return template('showitem', page=itemset[0])
        return HTTPError(404, "Page not found")
'''

__author__ = "CodeBeast357"
__version__ = '0.0.1'
__license__ = 'MIT'

### CUT HERE (see setup.py)

import unqlite
import inspect
import bottle

# PluginError is defined to bottle >= 0.10
if not hasattr(bottle, 'PluginError'):
    class PluginError(bottle.BottleException):
        pass
    bottle.PluginError = PluginError


class UnQLitePlugin(object):
    ''' This plugin passes an unqlite database handle to route callbacks
    that accept a `db` keyword argument. If a callback does not expect
    such a parameter, no connection is made. You can override the database
    settings on a per-route basis. '''

    name = 'unqlite'
    api = 2

    ''' python3 moves unicode to str '''
    try:
        unicode
    except NameError:
        unicode = str

    # Open mode flags.
    UNQLITE_OPEN_READONLY = 0x00000001
    UNQLITE_OPEN_READWRITE = 0x00000002
    UNQLITE_OPEN_CREATE = 0x00000004
    UNQLITE_OPEN_EXCLUSIVE = 0x00000008
    UNQLITE_OPEN_TEMP_DB = 0x00000010
    UNQLITE_OPEN_NOMUTEX = 0x00000020
    UNQLITE_OPEN_OMIT_JOURNALING = 0x00000040
    UNQLITE_OPEN_IN_MEMORY = 0x00000080
    UNQLITE_OPEN_MMAP = 0x00000100

    def __init__(self, filename=':mem:', flags=UNQLITE_OPEN_CREATE,
                 open_database=True, keyword='db'):
        self.filename = filename
        self.flags = flags
        self.open_database = open_database
        self.keyword = keyword

    def setup(self, app):
        ''' Make sure that other installed plugins don't affect the same
            keyword argument.'''
        for other in app.plugins:
            if not isinstance(other, UnQLitePlugin):
                continue
            if other.keyword == self.keyword:
                raise PluginError("Found another unqlite plugin with "
                                  "conflicting settings (non-unique keyword).")
            elif other.name == self.name:
                self.name += '_%s' % self.keyword

    def apply(self, callback, route):
        # hack to support bottle v0.9.x
        if bottle.__version__.startswith('0.9'):
            config = route['config']
            _callback = route['callback']
        else:
            config = route.config
            _callback = route.callback

        # Override global configuration with route-specific values.
        if "unqlite" in config:
            # support for configuration before `ConfigDict` namespaces
            g = lambda key, default: config.get('unqlite', {}).get(key, default)
        else:
            g = lambda key, default: config.get('unqlite.' + key, default)

        filename = g('filename', self.filename)
        flags = g('flags', self.flags)
        open_database = g('open_database', self.open_database)
        keyword = g('keyword', self.keyword)

        # Test if the original callback accepts a 'db' keyword.
        # Ignore it if it does not need a database handle.
        argspec = inspect.getargspec(_callback)
        if keyword not in argspec.args:
            return callback

        def wrapper(*args, **kwargs):
            # Connect to the database
            db = unqlite.UnQLite(filename, flags, open_database)
            # Add the connection handle as a keyword argument.
            kwargs[keyword] = db

            try:
                rv = callback(*args, **kwargs)
            except unqlite.UnQLiteError as e:
                db.rollback()
                raise bottle.HTTPError(500, "Database Error", e)
            except bottle.HTTPError:
                db.rollback()
                raise
            finally:
                db.close()
            return rv

        # Replace the route callback with the wrapped one.
        return wrapper

Plugin = UnQLitePlugin
