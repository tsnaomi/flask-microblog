#!usr/bin/env Python

import unittest
from sqlalchemy.exc import DataError
from microblog import (db, Post, write_post, read_posts, read_post,
                       client,)  # app
# with app.test_client()


class TestMicroblog(unittest.TestCase):

    def setUp(self):
        db.create_all()
        self.app = client
        self.spring = "Spring and All"
        self.imaginations = """\tThe imagination, intoxicated by prohibitions,
                        rises to drunken heights to destroy the world. Let it
                        rage, let it kill. The imagination is supreme."""

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_writePost(self):
        self.assertEqual(len(Post.query.all()), 0)
        write_post(self.spring, self.imaginations)
        post = Post.query.all()[0]
        self.assertEqual(len(Post.query.all()), 1)
        self.assertEqual(post.title, self.spring)
        self.assertEqual(post.body, self.imaginations)
        self.assertTrue(post.pub_date)

    def test_writePost_missing_values(self):
        with self.assertRaises(ValueError):
            write_post(None, None)
            write_post(self.spring, None)
            write_post(None, self.imaginations)

    def test_writePost_wordy_title(self):
        with self.assertRaises(DataError):
            write_post(self.imaginations, self.spring)

    def test_readPosts(self):
        for letter in "POEM":
            write_post(letter, self.imaginations)
        reverse_chron = "[POST: u'M', POST: u'E', POST: u'O', POST: u'P']"
        self.assertEqual(read_posts().__repr__(), reverse_chron)
        self.assertNotEqual(Post.query.all().__repr__(), reverse_chron)

    def test_readPosts_empty(self):
        self.assertEqual(read_posts().__repr__(), "[]")

    def test_readPost(self):
        for letter in "POEM":
            write_post(letter, self.imaginations)
        self.assertEqual(Post.query.all()[3], read_post(4))

    def test_readPost_bad_id(self):
        with self.assertRaises(KeyError):
            read_post(9)
            read_post("POEM")

    def test_listView(self):
        # with self.app.test_request_context('/'):
        #     assert self.app.request.path == '/'
        pass

    def test_listView_empty(self):
        # page = self.app.get('/')
        # assert '' in page.data
        pass

    def test_postView(self):
        # with self.app.test_client() as client:
        #     page = client.get('/posts/1')
        #     assert request.args['post'] == '1'
        pass

    def test_addPost(self):
        pass

    def test_login(self):
        pass

if __name__ == '__main__':
    unittest.main()
