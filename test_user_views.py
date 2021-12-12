"""User View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


import os
from unittest import TestCase

from models import db, connect_db, Message, User, Likes, Follows
from bs4 import BeautifulSoup

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app, CURR_USER_KEY

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class UserViewTestCase(TestCase):
    """Test views for users."""

    def setUp(self):
        """Setup test user and test data."""

        db.drop_all()
        db.create_all()

        self.client = app.test_client()

        self.testuser = User.signup(username='test_name', email='test@email.com', password='password', image_url='None')
        self.testuser_id = 6999
        self.testuser.id = self.testuser_id

        self.u1 = User.signup('user1', 'user1@email.com', 'password', None)
        self.u1_id = 1234
        self.u1.id = self.u1_id

        self.u2 = User.signup('user2', 'user2@email.com', 'password', None)
        self.u2_id = 5678
        self.u2.id = self.u2_id

        self.u3 = User.signup('name', 'user3@email.com', 'password', None)

        self.u4 = User.signup('first_name', 'user4@email.com', 'password', None)

        db.session.commit()

    def tearDown(self):
        """Clean up after test."""

        resp = super().tearDown()
        db.session.rollback()
        return resp
    
    def test_show_users(self):
        """Test that all users are in the data."""

        with self.client as c:
            resp = c.get('/users')

            self.assertIn('@test_name', str(resp.data))
            self.assertIn('@user1', str(resp.data))
            self.assertIn('@user2', str(resp.data))
            self.assertIn('@name', str(resp.data))
            self.assertIn('@first_name', str(resp.data))

    def test_search_user(self):
        """Test for searching for username."""

        with self.client as c:
            resp = c.get('/users?q=user')

            self.assertIn('@user1', str(resp.data))
            self.assertIn('@user2', str(resp.data))

            self.assertNotIn('@test_name', str(resp.data))
            self.assertNotIn('@name', str(resp.data))
            self.assertNotIn('@first_name', str(resp.data))

    def test_show_user(self):
        """Test showing a specific user based on id."""

        with self.client as c:
            resp = c.get(f'/users/{self.testuser_id}')

            self.assertEqual(resp.status_code, 200)

            self.assertIn('@testuser', str(resp.data))
    
    def setup_likes_for_test(self):
        """Setup data to test likes."""

        msg1 = Message(text='I am the first test message', user_id=self.testuser_id)
        msg2 = Message(text='I love bbq', user_id=self.testuser_id)
        msg3 = Message(id=9999, text='My favorite color is blue', user_id=self.u1_id)

        db.session.add([msg1, msg2, msg3])
        db.session.commit()

        l1 = Likes(user_id=self.testuser_id, message_id=9999)

        db.session.add(l1)
        db.session.commit()

    def test_show_user_details(self):
        """Test the view of a user with likes."""

        self.setup_likes_for_test()

        with self.client as c:
            resp = c.get(f'/users/{self.testuser_id}')

            self.assertEqual(resp.status_code, 200)

            self.assertIn('@testuser', str(resp.data))
            soup = BeautifulSoup(str(resp.data), 'html.parser')
            found = soup.find_all('li', {'class': 'stat'})

            self.assertIn('2', found[0].text)

            self.assertIn('0', found[1].text)

            self.assertIn('0', found[2].text)

            self.assertIn('1', found[3].text)

    def test_add_like(self):
        """Test to add a like by the user."""

        msg = Message(id=2000, text='My dog hates snow', user_id=self.u1_id)

        db.session.add(msg)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as session:
                session[CURR_USER_KEY] = self.testuser_id

            resp = c.post('/users/add_like/2000', follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            likes = Likes.query.filter(likes.message_id==2000).all()
            self.assertEqual(len(likes), 1)
            self.assertEqual(likes[0].user_id, self.testuser_id)

    def test_remove_like(self):
        """Test to remove likes by a user."""

        self.setup_likes_for_test()

        msg = Message.query.filter(Message.text=='I am the first test message').one()

        self.assertIsNotNone(msg)
        self.assertNotEqual(msg.user_id, self.testuser_id)

        likes = Likes.query.filter(Likes.user_id==self.testuser_id and Likes.message_id==msg).one()

        self.assertIsNotNone(likes)

        with self.client as c:
            with c.session_transaction as session:
                session[CURR_USER_KEY] = self.testuser_id

            resp = c.post(f'/users/add_like/{message.id}', follow_redirect=True)
            self.assertEqual(resp.status_code, 200)

            like = Likes.query.filter(Likes.message_id==m.id),all()

            self.assertEqual(len(like), 0)

    def test_unauthicated_like(self):
        """Test to like without being logged in."""

        self.setup_likes_for_test()

        message = Message.query.filter(Message.text=='I am the first test message').one()
        self.assertIsNotNone(message)

        total_likes = Likes.query.count()

        with self.client as c:
            resp = c.post(f'/users/add_like/{message.id}')
            self.assertEqual(resp.status_code, 200)

            self.assertIn('Access unauthorized', str(resp.data))

            self.assertEqual(total_likes, Likes.query.count())

    def setup_test_followers(self):
        """Setup followers to test."""

        follower1 = Follows(user_being_followed_id=self.u1_id, user_following_id=self.testuser_id)
        follower2 = Follows(user_being_followed_id=self.u2_id, user_following_id=self.testuser_id)
        follower3 = Follows(user_being_followed_id=self.testuser_id, user_following_id=self.u1_id)

        db.session.add_all([follower1, follower2, follower3])
        db.session.commit()

    def test_user_follows(self):
        """Show how many follows test user and how many test user is following."""

        self.setup_test_followers()

        with self.client as c:
            resp = c.get(f'/users/{self.testuser_id}')

            self.assertEqual(resp.status_code, 200)

            self.assertIn('@testuser', str(resp.data))

            soup = BeautifulSoup(str(resp.data), 'html.parser')
            found = soup.find_all('li', {'class': 'stat'})
            self.assertEqual(len(found), 4)

            self.assertIn('0', found[0].text)
            self.assertIn('2', found[1].text)
            self.assertIn('1', found[2].text)
            self.assertIn('0', found[3].text)

    def test_show_following(self):
        """Show the people who are following the test user."""

        self.setup_test_followers()

        with self.client as c:
            with c.session_transaction() as session:
                session[CURR_USER_KEY] = self.testuser_id

            resp = c.get(f'/users/{self.testuser_id}/following')

            self.assertEqual(resp.status_code, 200)
            self.assertIn('@user1', str(resp.data))
            self.assertIn('@user2', str(resp.data))
            self.assertNotIn('@name', str(resp.data))
            self.assertNotIn('@first_name', str(resp.data))

    def test_show_followers(self):
        """Show the people the test user is following."""

        self.setup_test_followers()

        with self.client as c:
            with c.session_transaction as session:
                session[CURR_USER_KEY] = self.testuser_id
            
            resp = c.get(f'/users/{self.testuser_id}/followers')

            self.assertIn('@user1', str(resp.data))
            self.assertNotIn('@user2', str(resp.data))
            self.assertNotIn('@name', str(resp.data))
            self.assertNotIn('@first_name', str(resp.data))

    def test_unauthorized_following_access(self):
        """Test unauthorized trying to access and see who test user is following."""

        self.setup_test_followers()

        with self.client as c:

            resp = c.get(f'/users/{self.testuser_id}/following', follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertNotIn('@user1', str(resp.data))
            self.assertIn('Access unauthorized', str(resp.data))

    def test_unauthorized_followers_access(self):
        """Test unauthorized trying to access and see who follows test user."""

        self.setup_test_followers()

        with self.client as c:

            resp = c.get(f'/users/{self.testuser_id}/followers', follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertNotIn('@user1', str(resp.data))
            self.assertIn('Access unauthorized', str(resp.data))