#!usr/bin/env Python

import unittest
from microblog import (db, app, session, Post, Author, read_posts, write_post,
                       read_post)  # Registration
from sqlalchemy.exc import DataError


class TestMicroblog_login(unittest.TestCase):

    def setUp(self):
        db.drop_all()
        db.create_all()
        self.app = app.test_client()
        self.context = app.test_request_context()
        self.email = 'redwheelbarrow@WCW.edu'
        self.author = 'WilliamsCarlosWilliams'
        self.password = 'glazedwithrain'
        self.spring = 'Spring and All'
        self.imaginations = '''\tThe imagination, intoxicated by prohibitions,
                        rises to drunken heights to destroy the world. Let it
                        rage, let it kill. The imagination is supreme.'''
        AUTHOR = Author(self.email, self.author, self.password)
        db.session.add(AUTHOR)
        db.session.commit()
        self.context.push()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.context.pop()

    def test_loginView_NAY(self):
        with self.app as client:
            response = client.post('/login', data=dict(
                username=self.spring,
                password=self.imaginations),
                follow_redirects=True)
        self.assertIn('Invalid username or password', response.data)

    def test_loginView_YEAAAAAA(self):
        with self.app as client:
            response = client.post('/login', data=dict(
                username=self.author,
                password=self.password),
                follow_redirects=True)
        self.assertIn('You are now logged in as WilliamsCarlosWilliams',
                      response.data)

    def test_logoutView(self):
        with self.app as client:
            client.post('/login', data=dict(
                username=self.author,
                password=self.password),
                follow_redirects=True)
            response = client.get('/logout', follow_redirects=True)
        self.assertIn('You have been logged out.', response.data)


class TestMicroblog_everything_else(unittest.TestCase):

    def setUp(self):
        db.drop_all()
        db.create_all()
        self.app = app.test_client()
        self.context = app.test_request_context()
        self.email = 'redwheelbarrow@WCW.edu'
        self.author = 'WilliamCarlosWilliams'
        self.password = 'glazedwithrain'
        self.spring = 'Spring and All'
        self.imaginations = '''\tThe imagination, intoxicated by prohibitions,
                        rises to drunken heights to destroy the world. Let it
                        rage, let it kill. The imagination is supreme.'''
        self.AUTHOR = Author(self.email, self.author, self.password)
        db.session.add(self.AUTHOR)
        db.session.commit()
        self.context = app.test_request_context()
        self.context.push()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.context.pop()

    def POETRY(self):
        for letter in 'POEM':
            session['current_user'] = self.author
            write_post(letter, self.imaginations)

    def LOGIN(self, USERNAME, PASSWORD):
        with self.app as client:
            response = client.post('/login', data=dict(
                username=USERNAME,
                password=PASSWORD),
                follow_redirects=True)
            return response

    def test_writePost(self):
        self.LOGIN(self.author, self.password)
        session['current_user'] = self.author
        write_post(self.spring, self.imaginations)
        post = Post.query.all()[0]
        self.assertEqual(len(Post.query.all()), 1)
        self.assertEqual(post.title, self.spring)
        self.assertEqual(post.body, self.imaginations)
        self.assertTrue(post.pub_date)

    def test_writePost_missing_values(self):
        self.LOGIN(self.author, self.password)
        with self.assertRaises(ValueError):
            write_post(None, None)
            write_post(self.spring, None)
            write_post(None, self.imaginations)

    def test_writePost_wordy_title(self):
        self.LOGIN(self.author, self.password)
        session['current_user'] = self.author
        with self.assertRaises(DataError):
            write_post(self.imaginations, self.spring)

    def test_readPosts(self):
        self.POETRY()
        reverse_chron = "[POST: u'M', POST: u'E', POST: u'O', POST: u'P']"
        self.assertEqual(read_posts().__repr__(), reverse_chron)
        self.assertNotEqual(Post.query.all().__repr__(), reverse_chron)

    def test_readPosts_empty(self):
        self.assertEqual(read_posts().__repr__(), '[]')

    def test_readPost(self):
        self.POETRY()
        self.assertEqual(Post.query.all()[3], read_post(4))

    def test_readPost_bad_id(self):
        with self.assertRaises(KeyError):
            read_post(9)
            read_post('POEM')

    def test_listView(self):
        self.POETRY()
        posts = Post.query.all()
        with self.app as client:
            response = client.get('/')
        for post in posts:
            self.assertIn(post.title, response.data)

    def test_listView_empty(self):
        with self.app as client:
            response = client.get('/')
        Williams = '''To refine, to clarify, to intensify that eternal moment in which we alone live there is but a single force&#151the imagination.'''
        self.assertIn(Williams, response.data)

    def test_detailsView(self):
        self.POETRY()
        posts = Post.query.all()
        for post in posts:
            with self.app as client:
                response = client.get('/post/%s' % str(post.id))
            self.assertIn(post.title, response.data)
            self.assertIn(post.body, response.data)

    def test_detailsView_nonexistent(self):
        with self.app as client:
            response = client.get('/post/20')
            self.assertIn('404: This page does not exist.', response.data)

    def test_addView_get(self):
        self.LOGIN(self.author, self.password)
        with self.app as client:
            response = client.get('/add')
        template = "<form action='/add' method=post class=add-post>"
        self.assertIn(template, response.data)

    # def test_registrationView_YEAAAAAA(self):
    #     pass

    def test_attempt_add_while_signed_in(self):
        self.LOGIN(self.author, self.password)
        with self.app as client:
            response = client.post('/add', data=dict(
                title=self.spring,
                body=self.imaginations),
                follow_redirects=True)
        self.assertIn(self.spring, response.data)
        self.assertIn(self.imaginations, response.data)
        self.assertEqual(len(Post.query.all()), 1)

    def test_attempt_add_while_signed_out(self):
        self.POETRY()
        with self.app as client:
            response = client.post('/add', data=dict(
                title=self.spring,
                body=self.imaginations),
                follow_redirects=True)
        self.assertIn('401: Log the fuck in.', response.data)  # apologies

    def test_attempt_add_with_missing_values(self):
        self.LOGIN(self.author, self.password)
        with self.app as client:
            response = client.post('/add', data=dict(
                title=None,
                body=self.imaginations),
                follow_redirects=True)
        self.assertIn('Please provide both a title and body', response.data)
        with self.app as client:
            response = client.post('/add', data=dict(
                title=self.spring,
                body=None),
                follow_redirects=True)
        self.assertIn('Please provide both a title and body', response.data)

if __name__ == '__main__':
    unittest.main()
