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
    assert response['statusCode'] == 200, f"Expected 200, got {response['statusCode']}"
    assert 'result' in response['body'], "Response body should contain 'result'"
    assert isinstance(response['body']['result'], list), "result should be a list"
    assert len(response['body']['result']) <= 10, "Result should not exceed page size of 10"
    
    NUM_PAGES = 5
    for page in range(1, NUM_PAGES + 1):
        continuation_key = response['body'].get('context', {}).get('continuation_key', None)
        if continuation_key is None:
            break
        query_body['context']['continuation_key'] = continuation_key
        response = execute_endpoint('ads/query', method='POST', body=query_body, auth=True)
        assert response['statusCode'] == 200, f"Expected 200, got {response['statusCode']}"
        assert 'result' in response['body'], "Response body should contain 'result'"
        assert isinstance(response['body']['result'], list), "result should be a list"
        assert len(response['body']['result']) <= 10, "Result should not exceed page size of 10"

def test_query_by_activation_code_with_session():
    activation_codes = ["d4e0fd","cbdd7a","4f6615","f27409","12ec0f","4a627c","1ffe50","96d011","bb24d5","3171b1","dd15f8","a8cbd6","f0a428","bd69cf","5714f2","0a4f33","95d224","ac48d0","5e6bc4","9c89e3","42fd43","aa613f","af242c","099f01","cba5a4","43b29a","e54d7d","6b08cf","c81492","e6e0c5","8ada99","7030f0","c9cb8f","0d89a8","427965","9b1acb","c04479","1e1420","aa6844","d61940","d04299","2ec4c4","bf447d","840fdc","b58980","b39d73","define","5323db","6b33ce","2b3c09","19135c","96d896","f58cfc","aebc2f","1d5e3a","947bce","0a6517","c548b2","14b293","b8d379","134ba5","0358a4","905909","fd8344","43c163","0566d8","1fa006","6d3557","2330dc","e725dd","262295","79f51c","e5ef2f","bf9fbf","c96ea1","641cd8","da1104","77eeb5","e28f31","d42990","7fb962","603ed2","16a6ac","2fd016","87543a","be31ee","f831ae","529d23","eee428","0cfe07","86bdcc","2a7c64","4e56c2","d78676","496d36","4be3b1","fa356c","3a5663","1e2ccd","7eae08","3dcf5a","d13b6d","3f3199","5299bd","185c08","3d1165","8fc58f","dcfc18","ee871d","f477a1","eabf26","4efbd8","33cc03","aa9d8f","055a20","a82837","d5ab66","2190ae","9996a0","fd64e6","0faa7c","ef07a6","d01d73","0d24b0","ccafc9","3439ac","565210","1f3b45","d60d05","99ef34","a95908","4ffcba","90c3b9","fb8de1","10a172","e08c94","76a5a5","b61aec","14bf15","7fc292","ad8682","d0a3d4","dbbcbe","725b71","262e80","58d8ca","b9a9e6","b06713","ca6dc1","6e4521","776431","b5fe28","e16dbb","35c350","48202a","4dab5c","b2c3d4","61b6dc","85e836","fb4c1a","ac4f04","5afd55","4205a6","2e25b5","5d67e5","520d5a","5c1298","f48a94","7c5764","da922e","c6746d","3d4b97","0babb3","419528","925e5c","526357","078a3a","08c836","d36ac2","14ec77","cc0657","0664f2","22f51b","7f49f9","0a8916","2b9b47","78d277","f36f00","63f81d","1c8940","c4bd5c","942917","c2340f","05b055","463390","32cf50","3a981c","13ae80","b517aa","f02715","91ef6f","c1f342","41ddb5","d90422","e8a727","5ee7fa","dc784e","93c1ec","06fbdb","83658f","c41668","fd59ad","90403f","ab434e","6aa197","2b6066","66be2b","644698","7b1342","39b009","7cefff","f05ccd","24302e","e6594b","4a9d80","2b8f5d","6cfef0","feb3c5","4c52ef","4ad96f","58abd5","c73c41","9b0f05","637a75","4d2302","d9eab0","5f7b19","ef2d92","543bb8","91dc6f","3bd098","596d65","8c389d","4e0951","b32650","c760d9","188e54","c5ba1e","b9c72b","bc73b0","0608d0","d8941d","ffe1f7","3f2104","4ce00c","67a783","45d409","2f9567","c7d80b","3427cb","17c39c","83aac2","17e076","e2c458","40e672","0184ea","9b2355","f89d81","125f02","381f2b","028934","8693d1","9e6a02","3c8fac","04be74","c5da95","495705","53ce65","a2a3b8","4cd95c","5d2678","18f466","1f51c6","648ea7","52f1ae","0a96da","375cc9","45068a","1923b6","842b0f","b1efe7","efae54","b6fcb5","b574f0","500873","da3182","b6f1aa","93dfba","a80482","bc2c1c","2e41e8","96b10c","3affbd","a278b1","5b3867","4da569","6f256d","71585b","398735","ae6161","ff7556","ea7016","f97116","43c313","165f7e","ea1797","3a121a","fb5f37","35283b","d8a08d","50faad","a3c721","ec4a4f","867a04","e93ef1","563a6e","460bf2","01f92d","39bc69","7a1f59","ca0877","d83187","bf47fe","e1df2a","13fa01","d67575","e41b51","e4da3a","2e8235","5b6a34","ae45e6","da812f","a29027","bc2f2b","5ca6cd"]
    PAGE_SIZE = 1000
    
    query_body = {
        'method': 'OBSERVER_ID_CONTAINS',
        'args': activation_codes,
        'context': {
            'page_size': PAGE_SIZE,
            'full_query': True,
        }
    }
    
    session_response = execute_endpoint('ads/query/new-session', method='GET', auth=True)
    session_id = session_response['body']['session_id']
    query_body['session_id'] = session_id
    response = execute_endpoint('ads/query', method='POST', body=query_body, auth=True)
    assert response['statusCode'] == 200, f"Expected 200, got {response['statusCode']}"
    assert 'result' in response['body'], "Response body should contain 'result'"
    assert isinstance(response['body']['result'], list), "result should be a list"
    assert len(response['body']['result']) <= PAGE_SIZE, f"Result should not exceed page size of {PAGE_SIZE}"
    assert len(response['body']['result']) > 0, "Result should not be empty"
    
    queries_completed = 1
    continuation_key = response['body'].get('context', {}).get('continuation_key', None)
    while continuation_key is not None:
        query_body['context']['continuation_key'] = continuation_key
        response = execute_endpoint('ads/query', method='POST', body=query_body, auth=True)
        assert response['statusCode'] == 200, f"Expected 200, got {response['statusCode']}"
        assert 'result' in response['body'], "Response body should contain 'result'"
        assert isinstance(response['body']['result'], list), "result should be a list"
        assert len(response['body']['result']) <= PAGE_SIZE, f"Result should not exceed page size of {PAGE_SIZE}"
        continuation_key = response['body'].get('context', {}).get('continuation_key', None)
        queries_completed += 1

def test_query_between_dates_with_session():
    PAGE_SIZE = 1000
    query_body = {
        'method': 'AND',
        'args': [
            {
                'method': 'DATETIME_AFTER',
                'args': ['1743948000000']  
            },
            {
                'method': 'DATETIME_BEFORE',
                'args': ['1746799200000'] 
            }
        ],
    }
    
    session_response = execute_endpoint('ads/query/new-session', method='GET', auth=True)
    session_id = session_response['body']['session_id']
    query_body['session_id'] = session_id
    
    response = execute_endpoint('ads/query', method='POST', body=query_body, auth=True)
    assert response['statusCode'] == 200, f"Expected 200, got {response['statusCode']}"
    assert 'result' in response['body'], "Response body should contain 'result'"
    assert isinstance(response['body']['result'], list), "result should be a list"
    assert len(response['body']['result']) <= PAGE_SIZE, f"Result should not exceed page size of {PAGE_SIZE}"
    assert len(response['body']['result']) > 0, "Result should not be empty"
    
    queries_completed = 1
    continuation_key = response['body'].get('context', {}).get('continuation_key', None)
    while continuation_key is not None:
        query_body['context'] = query_body.get('context', {})
        query_body['context']['continuation_key'] = continuation_key
        response = execute_endpoint('ads/query', method='POST', body=query_body, auth=True)
        assert response['statusCode'] == 200, f"Expected 200, got {response['statusCode']}"
        assert 'result' in response['body'], "Response body should contain 'result'"
        assert isinstance(response['body']['result'], list), "result should be a list"
        assert len(response['body']['result']) <= PAGE_SIZE, f"Result should not exceed page size of {PAGE_SIZE}"
        continuation_key = response['body'].get('context', {}).get('continuation_key', None)
        queries_completed += 1
    

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