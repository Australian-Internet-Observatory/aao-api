from base import execute_endpoint

def test_create_query_session():
    response = execute_endpoint('ads/query/new-session', method='GET', auth=True)
    assert response['statusCode'] == 200, f"Expected 200, got {response['statusCode']}"
    assert 'session_id' in response['body'], "Response body should contain 'session_id'"
    assert isinstance(response['body']['session_id'], str), "session_id should be a string"
    assert response['body']['session_id'] != '', "session_id should not be empty"
    
def test_one_page_query_with_session():
    # First, create a session
    session_response = execute_endpoint('ads/query/new-session', method='GET', auth=True)
    session_id = session_response['body']['session_id']
    
    # Now, use the session to query
    query_body = {
        'method': 'ANYTHING_CONTAINS',
        'args': [],
        'session_id': session_id
    }
    
    response = execute_endpoint('ads/query', method='POST', body=query_body, auth=True)
    print(response)
    assert response['statusCode'] == 200, f"Expected 200, got {response['statusCode']}"
    assert 'result' in response['body'], "Response body should contain 'result'"
    assert isinstance(response['body']['result'], list), "result should be a list"
    
def test_multiple_page_query_with_session():
    # First, create a session
    session_response = execute_endpoint('ads/query/new-session', method='GET', auth=True)
    session_id = session_response['body']['session_id']
    
    # Now, use the session to query with multiple pages
    query_body = {
        'method': 'ANYTHING_CONTAINS',
        'args': [],
        'session_id': session_id,
        'context': {
            'page_size': 10,
        }
    }
    
    response = execute_endpoint('ads/query', method='POST', body=query_body, auth=True)
    print(response)
    assert response['statusCode'] == 200, f"Expected 200, got {response['statusCode']}"
    assert 'result' in response['body'], "Response body should contain 'result'"
    assert isinstance(response['body']['result'], list), "result should be a list"
    assert len(response['body']['result']) <= 10, "Result should not exceed page size of 10"
    
    NUM_PAGES = 5
    for page in range(1, NUM_PAGES + 1):
        continuation_key = response['body'].get('context', {}).get('continuation_key', None)
        if continuation_key is None:
            print(f"No continuation key found on page {page}, stopping pagination.")
            break
        query_body['context']['continuation_key'] = continuation_key
        response = execute_endpoint('ads/query', method='POST', body=query_body, auth=True)
        print(response)
        assert response['statusCode'] == 200, f"Expected 200, got {response['statusCode']}"
        assert 'result' in response['body'], "Response body should contain 'result'"
        assert isinstance(response['body']['result'], list), "result should be a list"
        assert len(response['body']['result']) <= 10, "Result should not exceed page size of 10"
        
def test_full_query_with_session():
    # First, create a session
    session_response = execute_endpoint('ads/query/new-session', method='GET', auth=True)
    session_id = session_response['body']['session_id']
    PAGE_SIZE = 1000
    # Now, use the session to query with full query
    query_body = {
        'method': 'ANYTHING_CONTAINS',
        'args': [],
        'session_id': session_id,
        'context': {
            'page_size': PAGE_SIZE,
            'full_query': True,
        }
    }
    
    response = execute_endpoint('ads/query', method='POST', body=query_body, auth=True)
    assert response['statusCode'] == 200, f"Expected 200, got {response['statusCode']}"
    assert 'result' in response['body'], "Response body should contain 'result'"
    assert isinstance(response['body']['result'], list), "result should be a list"
    assert len(response['body']['result']) <= PAGE_SIZE, f"Result should not exceed page size of {PAGE_SIZE}"
    queries_completed = 1
    
    continuation_key = response['body'].get('context', {}).get('continuation_key', None)
    while continuation_key is not None:
        query_body['context']['continuation_key'] = continuation_key
        response = execute_endpoint('ads/query', method='POST', body=query_body, auth=True)
        assert response['statusCode'] == 200, f"Expected 200, got {response['statusCode']}"
        assert 'result' in response['body'], "Response body should contain 'result'"
        assert isinstance(response['body']['result'], list), "result should be a list"
        assert len(response['body']['result']) <= PAGE_SIZE, "Result should not exceed page size of {PAGE_SIZE}"
        
        continuation_key = response['body'].get('context', {}).get('continuation_key', None)
        queries_completed += 1
    print(f"Total queries completed: {queries_completed}")
    
def test_full_query_without_session():
    # Now, use the session to query with full query without session
    query_body = {
        'method': 'ANYTHING_CONTAINS',
        'args': []
    }
    
    response = execute_endpoint('ads/query', method='POST', body=query_body, auth=True)
    assert response['statusCode'] == 200, f"Expected 200, got {response['statusCode']}"
    assert 'result' in response['body'], "Response body should contain 'result'"
    assert isinstance(response['body']['result'], list), "result should be a list"