"""Integration tests for /ccl/* API endpoints.

These tests exercise the full request path through the local lambda handler,
including authentication, query-parameter parsing, database access, and
response serialisation.  They require a working database connection
(configured via config.ini) with the CCL tables already migrated.
"""

import json
import pytest
from apitests.base import execute_endpoint


# ---------------------------------------------------------------------------
# GET /ccl/entities
# ---------------------------------------------------------------------------

def test_get_ccl_entities_default():
    """Basic authenticated call returns 200 with expected shape."""
    response = execute_endpoint(endpoint="/ccl/entities", method="GET", auth=True)
    assert response["statusCode"] == 200, f"Expected 200, got {response['statusCode']}"
    body = response.get("body", {})
    assert body["success"] is True
    assert isinstance(body["entities"], list)
    assert "next_cursor" in body


def test_get_ccl_entities_with_limit():
    """Respects the limit query parameter."""
    response = execute_endpoint(endpoint="/ccl/entities?limit=5", method="GET", auth=True)
    assert response["statusCode"] == 200
    body = response["body"]
    assert len(body["entities"]) <= 5


def test_get_ccl_entities_with_cursor():
    """Cursor-based pagination returns results after the cursor."""
    # Fetch the first page
    first = execute_endpoint(endpoint="/ccl/entities?limit=1", method="GET", auth=True)
    assert first["statusCode"] == 200
    first_body = first["body"]
    entities = first_body.get("entities", [])
    if not entities:
        pytest.skip("No entities in database to paginate")

    cursor = entities[0]["id"]
    second = execute_endpoint(endpoint=f"/ccl/entities?limit=1&cursor={cursor}", method="GET", auth=True)
    assert second["statusCode"] == 200
    second_entities = second["body"]["entities"]
    if second_entities:
        assert second_entities[0]["id"] > cursor, "Cursor pagination should return IDs after the cursor"


def test_get_ccl_entities_filter_by_type():
    """Filter by entity type does not error."""
    response = execute_endpoint(endpoint="/ccl/entities?type=page", method="GET", auth=True)
    assert response["statusCode"] == 200
    body = response["body"]
    assert body["success"] is True
    for entity in body["entities"]:
        assert entity["type"] == "page"


def test_get_ccl_entities_unauthenticated():
    """Unauthenticated request returns 401."""
    response = execute_endpoint(endpoint="/ccl/entities", method="GET", auth=False)
    assert response["statusCode"] == 401


# ---------------------------------------------------------------------------
# GET /ccl/snapshots
# ---------------------------------------------------------------------------

def test_get_ccl_snapshots_default():
    """Basic authenticated call returns 200 with expected shape."""
    response = execute_endpoint(endpoint="/ccl/snapshots", method="GET", auth=True)
    assert response["statusCode"] == 200, f"Expected 200, got {response['statusCode']}"
    body = response.get("body", {})
    assert body["success"] is True
    assert isinstance(body["snapshots"], list)
    assert "next_cursor" in body


def test_get_ccl_snapshots_with_limit():
    """Respects the limit query parameter."""
    response = execute_endpoint(endpoint="/ccl/snapshots?limit=5", method="GET", auth=True)
    assert response["statusCode"] == 200
    body = response["body"]
    assert len(body["snapshots"]) <= 5


def test_get_ccl_snapshots_with_cursor():
    """Cursor-based pagination returns results after the cursor."""
    first = execute_endpoint(endpoint="/ccl/snapshots?limit=1", method="GET", auth=True)
    assert first["statusCode"] == 200
    snapshots = first["body"].get("snapshots", [])
    if not snapshots:
        pytest.skip("No snapshots in database to paginate")

    cursor = snapshots[0]["id"]
    second = execute_endpoint(endpoint=f"/ccl/snapshots?limit=1&cursor={cursor}", method="GET", auth=True)
    assert second["statusCode"] == 200
    second_snapshots = second["body"]["snapshots"]
    if second_snapshots:
        assert second_snapshots[0]["id"] > cursor


def test_get_ccl_snapshots_unauthenticated():
    """Unauthenticated request returns 401."""
    response = execute_endpoint(endpoint="/ccl/snapshots", method="GET", auth=False)
    assert response["statusCode"] == 401
