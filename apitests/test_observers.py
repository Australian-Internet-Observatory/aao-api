from base import execute_endpoint

def test_get_observer_csr_found():
    observer_id = "c1a56f0c-8775-4b5e-bc7e-8b9f41039cd5"
    url = f"/observers/{observer_id}/csr"
    response = execute_endpoint(url, method='GET', auth=True)
    assert response['statusCode'] == 200
    body = response['body']
    assert body['success'] is True
    assert 'presign_url' in body
    assert body['presign_url'] is not None
    assert body['presign_url'].startswith('https://')
    
def test_get_observer_csr_not_found():
    observer_id = "non-existent-observer"
    url = f"/observers/{observer_id}/csr"
    response = execute_endpoint(url, method='GET', auth=True)
    assert response['statusCode'] == 404
    body = response['body']
    assert body['success'] is False
    assert 'comment' in body