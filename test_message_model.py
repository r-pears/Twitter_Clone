"""Message model tests."""

# run these tests like:
#
#    python -m unittest test_message_model.py


import os
from unittest import TestCase
from sqlalchemy import exc

from models import db, User, Message, Follows, Likes

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

class MessageModelTestCase(TestCase):
    """Test models for messages."""

    def setUp(self):
        """Create test user and add test data."""

        db.drop_all()
        db.create_all()

        self.uid = 1111
        user = User.signup('testname', 'test@email.com', 'password', None)
        user.id = self.uid
        db.session.commit()

        self.user = User.query.get(self.uid)

        self.client = app.test_client()

    def tearDown(self):
        """Clean up after test."""

        resp = super().tearDown()
        db.session.rollback()
        return resp

    def test_message_model(self):
        """Test the message."""

        msg = Message(text='This is awesome', user_id=self.uid)

        db.session.add(msg)
        db.session.commit()

        self.assertEqual(len(self.user.messages), 1)
        self.assertEqual(self.user.messages[0].text, 'This is awesome')

    def test_message_like(self):
        """Test likes on messages."""

        msg1 = Message(text='This is awesome', user_id=self.uid)
        msg2 = Message(text='Second message', user_id=self.uid)

        u = User.signup('new_user', 'new@email.com', 'password', None)
        uid = 999
        u.id = uid

        db.session.add_all([msg1, msg2, u])
        db.session.commit()
        
        likes = Likes.query.filter(Likes.user_id == uid).all()

        self.assertEqual(len(likes), 2)
        self.assertEqual(likes[0].message_id, msg1.id)