import unittest
from app import app  # Import your Flask app

class TestApp(unittest.TestCase):
    def setUp(self):
        # Create a test client
        self.app = app.test_client()
        self.app.testing = True

    def test_addition(self):
        # Test the /add endpoint for addition
        response = self.app.get('/add?x=5&y=3')
        data = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data, '8')  # The expected result of 5 + 3

    def test_addition_invalid_input(self):
        # Test the /add endpoint with invalid input
        response = self.app.get('/add?x=5&y=invalid')
        self.assertEqual(response.status_code, 400)

if __name__ == '__main__':
    unittest.main()
