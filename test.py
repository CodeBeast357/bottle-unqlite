# -*- coding: utf-8 -*-
import os
import unittest
from unqlite import UnQLite
import tempfile

import bottle
from bottle.ext import unqlite

''' python3 moves unicode to str '''
try:
    unicode
except NameError:
    unicode = str


class UnQLiteTest(unittest.TestCase):

    def setUp(self):
        self.app = bottle.Bottle(catchall=False)
        _, filename = tempfile.mkstemp(suffix='.unqlite')
        self.plugin = self.app.install(unqlite.Plugin(filename=filename))

        self.conn = UnQLite(filename)
        self.conn.collection('todo').create()
        self.conn.close()

    def tearDown(self):
        pass
        # os.unlink(self.plugin.filename)

    def test_with_keyword(self):
        @self.app.get('/')
        def test(db):
            self.assertEqual(type(db), type(UnQLite(':mem:')))
        self._request('/')

    def test_without_keyword(self):
        @self.app.get('/')
        def test_1():
            pass
        self._request('/')

        @self.app.get('/2')
        def test_2(**kw):
            self.assertFalse('db' in kw)
        self._request('/2')

    def test_install_conflicts(self):
        self.app.install(unqlite.Plugin(keyword='db2'))

        @self.app.get('/')
        def test(db, db2):
            pass

        # I have two plugins working with different names
        self._request('/')

    def test_commit_on_redirect(self):
        @self.app.get('/')
        def test(db):
            self._insert_into(db)
            bottle.redirect('/')

        self._request('/')
        self.assert_records(1)

    def test_commit_on_abort(self):
        @self.app.get('/')
        def test(db):
            self._insert_into(db)
            bottle.abort()

        self._request('/')
        self.assert_records(0)

    def _request(self, path, method='GET'):
        return self.app({'PATH_INFO': path, 'REQUEST_METHOD': method},
                        lambda x, y: None)

    def _insert_into(self, db):
        db.collection('todo').store({ 'task': 'PASS' })

    def assert_records(self, count):
        self.conn.open()
        actual_count = len(self.conn.collection('todo').all())
        self.conn.close()
        self.assertEqual(count, actual_count)

if __name__ == '__main__':
    unittest.main()
