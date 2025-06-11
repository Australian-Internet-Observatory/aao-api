import unittest
from utils.opensearch import AdQuery

client = AdQuery()

class QueryTestCase(unittest.TestCase):
    def test_observer_id_contain_single(self):
        query = {
            "args": [
                "5ea"
            ],
            "method": "OBSERVER_ID_CONTAINS"
        }
        results = client.query_all(query)
        self.assertGreater(len(results), 0)
        
    def test_observer_id_empty(self):
        query = {
            "args": [],
            "method": "OBSERVER_ID_CONTAINS"
        }
        results = client.query_all(query)
        self.assertEqual(len(results), 0)
        
    def test_observer_id_contain_multiple(self):
        query = {
            "args": [
                "5ea",
                "49f"
            ],
            "method": "OBSERVER_ID_CONTAINS"
        }
        results = client.query_all(query)
        self.assertGreater(len(results), 0)
        
    def test_page_name_contains_single(self):
        query = {
            "args": [
                "Offenders Exposed"
            ],
            "method": "PAGE_NAME_CONTAINS"
        }
        results = client.query_all(query)
        self.assertGreater(len(results), 0)
    
    def test_page_name_contains_multiple(self):
        query = {
            "args": [
                "Offenders Exposed",
                "HelloFresh"
            ],
            "method": "PAGE_NAME_CONTAINS"
        }
        results = client.query_all(query)
        self.assertGreater(len(results), 0)
    
    def test_page_name_contains_partial(self):
        query = {
            "args": [
                "ell"
            ],
            "method": "PAGE_NAME_CONTAINS"
        }
        results = client.query_all(query)
        self.assertEqual(len(results), 0)
    
    def test_page_name_contains_case_insensitive(self):
        query = {
            "args": [
                "hellofresh"
            ],
            "method": "PAGE_NAME_CONTAINS"
        }
        results = client.query_all(query)
        self.assertGreater(len(results), 0)
    
    def test_datetime_after(self):
        query = {
            "args": [
                "1726408800000"
            ],
            "method": "DATETIME_AFTER"
        }
        results = client.query_all(query)
        self.assertGreater(len(results), 0)
        
    def test_datetime_before(self):
        query = {
            "args": [
                "1728223140000"
            ],
            "method": "DATETIME_BEFORE"
        }
        results = client.query_all(query)
        self.assertGreater(len(results), 0)

    def test_observation_id_contains_single(self):
        query = {
            "args": [
                "d8570" # fa**d8570**9-984e-4ccc-a0fd-8d5785930c95
            ],
            "method": "OBSERVATION_ID_CONTAINS"
        }
        results = client.query_all(query)
        self.assertGreater(len(results), 0)

    def test_observation_id_contains_multiple(self):
        query = {
            "args": [
                "d8570",
                "1a470c" # 9e434bdf-fbb9-474f-bb7d-f79**1a470c**777
            ],
            "method": "OBSERVATION_ID_CONTAINS"
        }
        results = client.query_all(query)
        self.assertGreater(len(results), 0)

    def test_categories_contains_single(self):
        query = {
            "args": [
                "POLITICAL"
            ],
            "method": "CATEGORIES_CONTAINS"
        }
        results = client.query_all(query)
        self.assertGreater(len(results), 0)
        
    def test_categories_contains_partial(self):
        query = {
            "args": [
                "POLI" # So POLITICAL should be included
            ],
            "method": "CATEGORIES_CONTAINS"
        }
        results = client.query_all(query)
        self.assertEqual(len(results), 0)

    def test_anything_contains_partial(self):
        query = {
            "args": [
                "aid for b" # So Paid for by should be included
            ],
            "method": "ANYTHING_CONTAINS"
        }
        results = client.query_all(query)
        self.assertEqual(len(results), 0)

    def test_anything_contains_single(self):
        query = {
            "args": [
                "Paid for by"
            ],
            "method": "ANYTHING_CONTAINS"
        }
        results = client.query_all(query)
        self.assertGreater(len(results), 0)

    def test_anything_contains_multiple(self):
        query = {
            "args": [
                "Paid for by",
                "Queensland"
            ],
            "method": "ANYTHING_CONTAINS"
        }
        results = client.query_all(query)
        self.assertGreater(len(results), 0)
    
    def test_anything_contains_long(self):
        query = {
            "args": [
                "Step into a world of sophisticated",
            ],
            "method": "ANYTHING_CONTAINS"
        }
        results = client.query_all(query)
        self.assertGreater(len(results), 0)
        
    def test_query_by_observer_id_v2(self):
        query = {
            "args": [
                "87a"
            ],
            "method": "OBSERVER_ID_CONTAINS"
        }
        results = client.query_all(query)
        print(results)
        self.assertGreater(len(results), 0)
        
if __name__ == '__main__':
    unittest.main()