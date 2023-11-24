import unittest
from app import app, db, User
from flask_login import current_user

class TestFlaskApp(unittest.TestCase):
    def setUp(self):
        self.app_context = app.app_context()
        self.app_context.push()
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        db.create_all()

        self.app = app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_register_and_login(self):
        with app.test_request_context():
            # Register a new user
            response = self.app.post('/register', data=dict(
                username='testuser',
                password='testpassword'
            ), follow_redirects=True)
            self.assertEqual(response.status_code, 200)

            # Log in with the registered user
            response = self.app.post('/login', data=dict(
                username='testuser',
                password='testpassword'
            ), follow_redirects=True)
            self.assertIn(b'Image Gallery', response.data)
            self.assertEqual(current_user.username, 'testuser')

    
if __name__ == '__main__':
    unittest.main()
