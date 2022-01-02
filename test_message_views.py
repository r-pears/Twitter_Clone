"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


import os
from unittest import TestCase

from models import db, connect_db, Message, User

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


class MessageViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)

        self.testuser_id = 9999
        self.testuser.id = self.testuser_id

        db.session.commit()

    def test_add_message(self):
        """Can use add a message?"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # Now, that session setting is saved, so we can have
            # the rest of ours test

            resp = c.post("/messages/new", data={"text": "Hello"})

            # Make sure it redirects
            self.assertEqual(resp.status_code, 302)

            msg = Message.query.one()
            self.assertEqual(msg.text, "Hello")

    def test_add_no_session(self):
        """Test if there is no session."""

        with self.client as c:
            resp = c.post('/messages/new', data={'text': 'Hello'}, follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('Access unauthorized', str(resp.data))

    def test_invalid_user(self):
        """Test if user doesn't exist."""

        with self.client as c:
            with c.session_transaction() as session:
                session[CURR_USER_KEY] = 2398577

            resp = c.post('/messages/new', data={'text': 'new message'}, follow_redirects=True)

            sef.assertEqual(resp.status_code, 200)
            self.assertIn('Access unauthorized', str(resp.data))

    def test_show_message(self):
        """Test show message."""

        msg = Message(id=2000, test='the latest message from me', user_id=self.testuser_id)

        db.session.add(msg)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as session:
                session[CURR_USER_KEY] = self.testuser.id

            message = Message.query.get(2000)

            resp = c.get(f'/messages/{message.id}')

            self.assertEqual(resp.status_code, 200)
            self.assertIn(message.text, str(resp.data))

    def test_invalid_message(self):
        """Test if the message id exists."""

        with self.client as c:
            with c.session_transaction() as session:
                session[CURR_USER_KEY] = self.testuser.id

            resp = c.get('/messages/9999999')

            self.assertEqual(resp.status_code, 404)

    def test_delete_message(self):
        """Test deleting message."""

        msg = Message(id=1212, text='a shitty message', user_id=self.testuser_id)

        db.session.add(msg)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as session:
                session[CURR_USER_KEY] = self.testuser.id

            resp = c.post('/messages/1212/delete', follow_redirects=True)

            self.assertEqual(resp.status_code, 200)

            message = Message.query.get(1212)

            self.assertIsNone(message)

    def test_unauthorized_delete_message(self):
        """Test if user trying to delete a message someone else wrote."""

        user = User.signup(username='username', email='test@mail.com', password='password', image_url=None)
        u.id = 12345

        msg = Message(id=1111, text='my message', user_id=self.testuser_id)

        db.session.add_all([user, msg])
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as session:
                sesion[CURR_USER_KEY] = 12345

            resp = c.post('/messages/1111/delete', follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('Access unauthorized', str(resp.data))

            message = Message.query.get(1111)
            self.assertIsNone(message)

    def test_delete_message_no_authentication(self):
        """Test to try and delete a message without authentication."""

        msg = Message(id=123, text='delete me', user_id=self.testuser_id)

        db.session.add(msg)
        db.session.commit()

        with self.client as c:
            resp = c.post('/messages/123/delete', follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('Access unauthorized', str(resp.data))

            message = Message.query.get(123)

            self.assertIsNotNone(message)
