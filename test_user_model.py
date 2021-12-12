"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase

from models import db, User, Message, Follows

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()


class UserModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        u1 = User.signup('user1', 'user1@email.com', 'password', None)
        u1id = 111
        u1.id = u1id

        u2 = User.signup('user2', 'user2@email.com', 'password', None)
        u2id = 222
        u2.id = u2id

        db.session.commit()

        u1 = User.query.get(u1id)
        u2 = User.quer.get(u2id)

        self.u1 = u1
        self.u1id = u1id

        self.u2 = u2
        self.u2id = u2id

        self.client = app.test_client()

    def tearDown(self):
        resp = super().tearDown()
        db.session.rollback()
        return resp

    def test_user_model(self):
        """Does basic model work?"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        # User should have no messages & no followers
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)

    def test_user_follow(self):
        """Test to check if user1 follows user 2."""

        self.u1.following.append(self.u2)
        db.session.commit()

        self.assertEqual(len(self.u2.following), 0)
        self.assertEqual(len(self.u2.followers), 1)
        self.assertEqual(len(self.u1.following), 1)
        self.assertEqual(len(self.u1.followers), 0)

        self.assertEqual(self.u2.followers[0].id, self.u1.id)
        self.assertEqual(self.u1.following[0].id, self.u2.id)

    def test_user_following(self):
        """Test user 1 is following user 2."""

        self.u1.following.append(self.u2)
        db.session.commit()

        self.assertTrue(self.u1.is_following(self.u2))
        self.assertFalse(self.u2.is_following(self.u1))
    
    def test_user_followed(self):
        """Test if user 2 is followed by user 1."""

        self.u1.following.append(self.u2)
        db.session.commit()

        self.assertTrue(self.u2.is_followed_by(self.u1))
        self.assertFalse(self.u1.is_followed_by(self.u2))
    
    def test_valid_signup(self):
        """Test if user succesfully signs up."""

        test_user = User.signup('testname', 'test@email.com', 'password', None)
        uid = 999
        test_user.id = uid
        db.session.commit()

        test_user = User.query.get(uid)
        self.assertIsNotNone(test_user)
        self.assertEqual(test_user.username, 'testname')
        self.assertEqual(test_user.email, 'test@email.com')
        self.assertEqual(test_user.password, 'password')
        self.assertTrue((test_user.password.startswith('$2b$')))

    def test_username_signup(self):
        """Test if username is valid."""

        invalid_user = User.signup(None, 'test@email.com', 'password', None)
        iuid = 1234
        invalid_user.id = iuid
        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()

    def test_email_signup(self):
        """Test if email is valid."""
        
        invalid_user = User.signup('testname', None, 'password', None)
        iuid = 1234
        invalid_user.id = iuid
        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()
    
    def test_password_signup(self):
        """Test if password is valid."""

        with self.assertRaises(ValueError) as context:
            User.signup('testname', 'test@email.com', '', None)
        
        with self.assertRaises(ValueError) as context:
            User.signup('testname', 'test@email.com', None, None)

    def test_valid_authentication(self):
        """Test authentication."""

        user = User.authenticate(self.u1.username, 'password')
        self.assertIsNotNone(user)
        self.assertEqual(u.id, self.u1id)
    
    def test_valid_username(self):
        """Test username authentication."""

        self.assertFalse(User.authenticate('invalid_username', 'password'))

    def test_valid_password(self):
        """Test password authentication."""

        self.assertFalse(User.authenticate(self.u1.username, 'invalid_password'))