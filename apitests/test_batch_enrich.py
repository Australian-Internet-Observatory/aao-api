"""
Test module for batch enrichment endpoints.

This module contains tests for the batch enrichment functionality,
including presigned URL generation for batch ad metadata requests.
"""

import pytest
import requests
from base import execute_endpoint
from enrich_target import ads


def test_batch_enrich_presign_success():
    """
    Test the batch enrich presign endpoint with valid data.
    
    This test verifies that the 'ads/batch/presign' endpoint correctly
    processes a batch of ads and returns a presigned URL for downloading
    the enriched metadata.
    """
    # Prepare the request data - use only first 10 ads for faster testing
    request_data = {
        "ads": ads[:10],
        "metadata_types": ['tags', 'attributes'],
    }
    
    # Execute the endpoint
    response = execute_endpoint(
        'ads/batch/presign',
        method='POST', 
        body=request_data,
        auth=True
    )
    
    # Verify successful response
    assert response['statusCode'] == 200
    assert response['body']['success'] is True
    assert 'presigned_url' in response['body']
    assert isinstance(response['body']['presigned_url'], str)
    assert len(response['body']['presigned_url']) > 0


def test_batch_enrich_presign_empty_ads():
    """
    Test the batch enrich presign endpoint with empty ads list.
    
    This test verifies that the endpoint handles empty ads list appropriately.
    """
    request_data = {
        "ads": [],
        "metadata_types": ['tags', 'attributes'],
    }
    
    response = execute_endpoint(
        'ads/batch/presign',
        method='POST', 
        body=request_data,
        auth=True
    )
    
    # The endpoint should handle empty ads list gracefully
    # The exact behavior depends on the implementation
    assert response['statusCode'] in [200, 400]


def test_batch_enrich_presign_invalid_metadata_types():
    """
    Test the batch enrich presign endpoint with invalid metadata types.
    
    This test verifies that the endpoint properly validates metadata types.
    """
    request_data = {
        "ads": ads[:5],
        "metadata_types": ['invalid_type'],
    }
    
    response = execute_endpoint(
        'ads/batch/presign',
        method='POST', 
        body=request_data,
        auth=True
    )
    
    # The endpoint should reject invalid metadata types
    # The exact status code depends on the implementation
    assert response['statusCode'] in [400, 422]


def test_batch_enrich_presign_missing_auth():
    """
    Test the batch enrich presign endpoint without authentication.
    
    This test verifies that the endpoint requires authentication.
    """
    request_data = {
        "ads": ads[:5],
        "metadata_types": ['tags', 'attributes'],
    }
    
    response = execute_endpoint(
        'ads/batch/presign',
        method='POST', 
        body=request_data,
        auth=False
    )
    
    # Should return 401 Unauthorized
    assert response['statusCode'] == 401
    assert response['body']['success'] is False


def test_batch_enrich_presign_all_metadata_types():
    """
    Test the batch enrich presign endpoint with all supported metadata types.
    
    This test verifies that the endpoint can handle all supported metadata types.
    """
    request_data = {
        "ads": ads[:5],
        "metadata_types": ['tags', 'attributes', 'rdo'],
    }
    
    response = execute_endpoint(
        'ads/batch/presign',
        method='POST', 
        body=request_data,
        auth=True
    )
    
    # Should succeed with all valid metadata types
    assert response['statusCode'] == 200
    assert response['body']['success'] is True
    assert 'presigned_url' in response['body']


def test_batch_enrich_presign_large_batch():
    """
    Test the batch enrich presign endpoint with a large batch of ads.
    
    This test verifies that the endpoint can handle larger batches.
    Marked as slow since it processes more data.
    """
    request_data = {
        "ads": ads,
        "metadata_types": ['tags', 'attributes'],
    }
    
    response = execute_endpoint(
        'ads/batch/presign',
        method='POST', 
        body=request_data,
        auth=True
    )
    
    # Should succeed with larger batch
    assert response['statusCode'] == 200
    assert response['body']['success'] is True
    assert 'presigned_url' in response['body']
    
def test_batch_enrich_attributes_one_ad():
    """
    Test the batch enrich attributes endpoint with a single ad.
    
    This test verifies that the endpoint can handle a request with only one ad.
    """
    request_data = {
        "ads": [
            {
                "ad_id": "13d7ab01-4e9a-4a3d-ac83-19a3705acecf",
                "observer_id": "d332600f-cd8c-490e-bbb5-f353b563a6ee",
                "timestamp": "1754435466166"
            },
        ],
        "metadata_types": ['attributes'],
    }
    response = execute_endpoint(
        'ads/batch/presign',
        method='POST', 
        body=request_data,
        auth=True
    )
    
    # Should succeed with single ad
    assert response['statusCode'] == 200
    assert response['body']['success'] is True
    assert 'presigned_url' in response['body']
    assert isinstance(response['body']['presigned_url'], str)
    assert len(response['body']['presigned_url']) > 0
    body = response['body']
    # Fetch the presigned URL
    response = requests.get(body['presigned_url'])
    
    content = response.json()
    
    # Check if the response is successful
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    # Check if the content is a list
    assert isinstance(content, list), f"Expected list, got {type(content)}"
    
    # Check if the ad is in the content
    assert len(content) == 1, f"Expected 1 ad, got {len(content)}"
    ad = content[0]
    
    print(ad)
    
    # Ensure the ad has the attributes we expect
    attributes = ad.get('metadata', {}).get('attributes')
    assert isinstance(attributes, dict), f"Expected attributes to be a dict, got {type(attributes)}"
    
    # Ensure the starred attribute is present
    assert 'starred' in attributes, f"Starred attribute not found in {attributes}"