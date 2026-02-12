"""Unit tests for routes/ccl.py helper functions.

These tests validate the pure-logic helpers without requiring a database
connection.
"""

import pytest
from routes.ccl import (
    _parse_pagination_params,
    _parse_filter_params,
    _needs_enrichment_join,
    _needs_observation_join,
    _serialize_entity,
    _serialize_snapshot,
    DEFAULT_LIMIT,
    MAX_LIMIT,
)


# ---------------------------------------------------------------------------
# _parse_pagination_params
# ---------------------------------------------------------------------------

class TestParsePaginationParams:

    def test_defaults_when_no_qs(self):
        event = {}
        limit, cursor = _parse_pagination_params(event)
        assert limit == DEFAULT_LIMIT
        assert cursor is None

    def test_defaults_when_qs_is_none(self):
        event = {"queryStringParameters": None}
        limit, cursor = _parse_pagination_params(event)
        assert limit == DEFAULT_LIMIT
        assert cursor is None

    def test_explicit_limit(self):
        event = {"queryStringParameters": {"limit": "50"}}
        limit, cursor = _parse_pagination_params(event)
        assert limit == 50
        assert cursor is None

    def test_limit_clamped_to_max(self):
        event = {"queryStringParameters": {"limit": "9999"}}
        limit, _ = _parse_pagination_params(event)
        assert limit == MAX_LIMIT

    def test_limit_clamped_to_min(self):
        event = {"queryStringParameters": {"limit": "0"}}
        limit, _ = _parse_pagination_params(event)
        assert limit == 1

    def test_invalid_limit_falls_back_to_default(self):
        event = {"queryStringParameters": {"limit": "abc"}}
        limit, _ = _parse_pagination_params(event)
        assert limit == DEFAULT_LIMIT

    def test_cursor_extracted(self):
        event = {"queryStringParameters": {"cursor": "some-uuid"}}
        _, cursor = _parse_pagination_params(event)
        assert cursor == "some-uuid"


# ---------------------------------------------------------------------------
# _parse_filter_params
# ---------------------------------------------------------------------------

class TestParseFilterParams:

    def test_empty_qs(self):
        assert _parse_filter_params({}) == {}

    def test_known_filters_extracted(self):
        qs = {
            "observation_id": "obs-1",
            "observer_id": "obr-1",
            "platform": "meta",
            "type": "page"
        }
        event = {"queryStringParameters": qs}
        filters = _parse_filter_params(event)
        assert filters == qs

    def test_unknown_params_ignored(self):
        event = {"queryStringParameters": {"unknown_key": "value", "type": "page"}}
        filters = _parse_filter_params(event)
        assert "unknown_key" not in filters
        assert filters["type"] == "page"


# ---------------------------------------------------------------------------
# _needs_enrichment_join / _needs_observation_join
# ---------------------------------------------------------------------------

class TestJoinDecisions:

    def test_no_join_for_entity_only_filters(self):
        assert _needs_enrichment_join({"type": "page"}) is False
        assert _needs_enrichment_join({"search": "foo"}) is False

    def test_join_for_observation_id(self):
        assert _needs_enrichment_join({"observation_id": "obs-1"}) is True

    def test_join_for_platform(self):
        assert _needs_enrichment_join({"platform": "meta"}) is True

    def test_join_for_date_filters(self):
        assert _needs_enrichment_join({"scrape_started_after": "100"}) is False
        assert _needs_enrichment_join({"scrape_completed_before": "200"}) is False

    def test_observation_join_only_for_observer_id(self):
        assert _needs_observation_join({"observer_id": "obr-1"}) is True
        assert _needs_observation_join({"observation_id": "obs-1"}) is False
        assert _needs_observation_join({}) is False


# ---------------------------------------------------------------------------
# Serialisation helpers
# ---------------------------------------------------------------------------

class _FakeEntity:
    """Mimics AdvertisingEntityORM for serialisation tests."""
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class TestSerializeEntity:

    def test_basic_serialisation(self):
        entity = _FakeEntity(
            id="e-1",
            ccl_enrichment_id="enr-1",
            source_id="src-1",
            type="page",
            data={"name": "Test Page", "extra": "value"},
        )
        result = _serialize_entity(entity)
        assert result == {
            "id": "e-1",
            "ccl_enrichment_id": "enr-1",
            "source_id": "src-1",
            "type": "page",
            "name": "Test Page",
            "data": {"name": "Test Page", "extra": "value"},
        }

    def test_missing_name_in_data(self):
        entity = _FakeEntity(
            id="e-2",
            ccl_enrichment_id="enr-2",
            source_id=None,
            type="keyword",
            data={"keyword": "shoes"},
        )
        result = _serialize_entity(entity)
        assert result["name"] is None

    def test_none_data(self):
        entity = _FakeEntity(
            id="e-3",
            ccl_enrichment_id="enr-3",
            source_id=None,
            type="location",
            data=None,
        )
        result = _serialize_entity(entity)
        assert result["data"] == {}
        assert result["name"] is None


class TestSerializeSnapshot:

    def test_basic_serialisation(self):
        snapshot = _FakeEntity(
            id="s-1",
            ccl_enrichment_id="enr-1",
            source_id="src-1",
            data={"title": "Ad snapshot"},
        )
        result = _serialize_snapshot(snapshot)
        assert result == {
            "id": "s-1",
            "ccl_enrichment_id": "enr-1",
            "source_id": "src-1",
            "data": {"title": "Ad snapshot"},
        }

    def test_none_data(self):
        snapshot = _FakeEntity(
            id="s-2",
            ccl_enrichment_id="enr-2",
            source_id=None,
            data=None,
        )
        result = _serialize_snapshot(snapshot)
        assert result["data"] == {}
