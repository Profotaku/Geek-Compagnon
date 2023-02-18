import unittest
import recommandations
import flask
import json
class Test_Recommandation(unittest.TestCase):
    def test_recommandation(self):
        app = flask.Flask(__name__)
        app.config['TESTING'] = True
        with app.test_request_context():
            result = recommandations.recommandations(1, 5)
            data = json.loads(result.get_data(as_text=True))
            self.assertEqual(result.status_code, 200)
            self.assertIn('recommandations', data)
            self.assertIsInstance(data['recommandations'], list)


if __name__ == '__main__':
    unittest.main()
