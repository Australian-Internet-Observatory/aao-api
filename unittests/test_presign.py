"""Unit tests for utils/presign.py — S3 URI → pre-signed URL replacement."""

import pytest
from unittest.mock import MagicMock

from utils.presign import replace_s3_uris, _presign_s3_uri


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_mock_client(prefix: str = "https://presigned.example.com/"):
    """Return a mock S3 client whose ``generate_presigned_url`` returns a
    deterministic URL derived from the bucket and key."""
    client = MagicMock()

    def _fake_presign(ClientMethod, Params, ExpiresIn):
        bucket = Params["Bucket"]
        key = Params["Key"]
        return f"{prefix}{bucket}/{key}?signed=1"

    client.generate_presigned_url.side_effect = _fake_presign
    return client


# ---------------------------------------------------------------------------
# _presign_s3_uri
# ---------------------------------------------------------------------------

class TestPresignS3Uri:

    def test_basic_uri(self):
        client = _make_mock_client()
        result = _presign_s3_uri("s3://my-bucket/path/to/file.jpg", client=client)
        assert result == "https://presigned.example.com/my-bucket/path/to/file.jpg?signed=1"
        client.generate_presigned_url.assert_called_once_with(
            ClientMethod="get_object",
            Params={"Bucket": "my-bucket", "Key": "path/to/file.jpg"},
            ExpiresIn=3600,
        )

    def test_uri_with_nested_path(self):
        client = _make_mock_client()
        result = _presign_s3_uri("s3://bucket/a/b/c/d.mp4", client=client)
        assert result == "https://presigned.example.com/bucket/a/b/c/d.mp4?signed=1"

    def test_uri_with_no_key(self):
        """Edge case: s3://bucket/ (empty key) — should still produce a URL."""
        client = _make_mock_client()
        result = _presign_s3_uri("s3://bucket/", client=client)
        assert "bucket" in result


# ---------------------------------------------------------------------------
# replace_s3_uris — string values
# ---------------------------------------------------------------------------

class TestReplaceS3UrisStrings:

    def test_s3_string_replaced(self):
        client = _make_mock_client()
        result = replace_s3_uris("s3://b/key.png", client=client)
        assert result.startswith("https://presigned.example.com/")

    def test_https_string_unchanged(self):
        client = _make_mock_client()
        result = replace_s3_uris("https://cdn.example.com/img.png", client=client)
        assert result == "https://cdn.example.com/img.png"
        client.generate_presigned_url.assert_not_called()

    def test_plain_string_unchanged(self):
        result = replace_s3_uris("hello world")
        assert result == "hello world"

    def test_empty_string_unchanged(self):
        result = replace_s3_uris("")
        assert result == ""


# ---------------------------------------------------------------------------
# replace_s3_uris — non-string scalars
# ---------------------------------------------------------------------------

class TestReplaceS3UrisScalars:

    def test_int_passthrough(self):
        assert replace_s3_uris(42) == 42

    def test_float_passthrough(self):
        assert replace_s3_uris(3.14) == 3.14

    def test_none_passthrough(self):
        assert replace_s3_uris(None) is None

    def test_bool_passthrough(self):
        assert replace_s3_uris(True) is True


# ---------------------------------------------------------------------------
# replace_s3_uris — dicts
# ---------------------------------------------------------------------------

class TestReplaceS3UrisDicts:

    def test_flat_dict(self):
        client = _make_mock_client()
        data = {
            "image_url": "s3://bucket/img.jpg",
            "title": "Hello",
            "count": 5,
        }
        result = replace_s3_uris(data, client=client)
        assert result["image_url"].startswith("https://presigned.example.com/")
        assert result["title"] == "Hello"
        assert result["count"] == 5

    def test_nested_dict(self):
        client = _make_mock_client()
        data = {
            "media": {
                "thumbnail": "s3://bucket/thumb.jpg",
                "video": "s3://bucket/vid.mp4",
            },
            "name": "Ad",
        }
        result = replace_s3_uris(data, client=client)
        assert result["media"]["thumbnail"].startswith("https://presigned.example.com/")
        assert result["media"]["video"].startswith("https://presigned.example.com/")
        assert result["name"] == "Ad"

    def test_empty_dict(self):
        assert replace_s3_uris({}) == {}


# ---------------------------------------------------------------------------
# replace_s3_uris — lists
# ---------------------------------------------------------------------------

class TestReplaceS3UrisLists:

    def test_list_of_s3_uris(self):
        client = _make_mock_client()
        data = ["s3://b/a.jpg", "s3://b/b.jpg"]
        result = replace_s3_uris(data, client=client)
        assert all(r.startswith("https://presigned.example.com/") for r in result)

    def test_mixed_list(self):
        client = _make_mock_client()
        data = ["s3://b/a.jpg", "https://cdn.example.com/b.jpg", 42, None]
        result = replace_s3_uris(data, client=client)
        assert result[0].startswith("https://presigned.example.com/")
        assert result[1] == "https://cdn.example.com/b.jpg"
        assert result[2] == 42
        assert result[3] is None

    def test_empty_list(self):
        assert replace_s3_uris([]) == []


# ---------------------------------------------------------------------------
# replace_s3_uris — deeply nested / realistic JSONB
# ---------------------------------------------------------------------------

class TestReplaceS3UrisComplex:

    def test_realistic_ccl_data(self):
        """Simulate a realistic advertising entity JSONB blob."""
        client = _make_mock_client()
        data = {
            "name": "Test Advertiser",
            "profile_picture_url": "s3://fta-mobile-observations-v2-ccl/media/profile.jpg",
            "ads": [
                {
                    "id": "ad-1",
                    "creative": {
                        "image": "s3://fta-mobile-observations-v2-ccl/media/ad1.jpg",
                        "video": "s3://fta-mobile-observations-v2-ccl/media/ad1.mp4",
                    },
                    "link": "https://example.com/landing",
                },
                {
                    "id": "ad-2",
                    "creative": {
                        "image": "https://cdn.external.com/img.jpg",
                    },
                },
            ],
            "metadata": {
                "scraped_at": 1700000000,
                "source": "meta",
            },
        }
        result = replace_s3_uris(data, client=client)

        # S3 URIs replaced
        assert result["profile_picture_url"].startswith("https://presigned.example.com/")
        assert result["ads"][0]["creative"]["image"].startswith("https://presigned.example.com/")
        assert result["ads"][0]["creative"]["video"].startswith("https://presigned.example.com/")

        # Non-S3 values unchanged
        assert result["name"] == "Test Advertiser"
        assert result["ads"][0]["link"] == "https://example.com/landing"
        assert result["ads"][1]["creative"]["image"] == "https://cdn.external.com/img.jpg"
        assert result["metadata"]["scraped_at"] == 1700000000

    def test_no_s3_uris_means_no_presign_calls(self):
        client = _make_mock_client()
        data = {"name": "Clean", "url": "https://example.com"}
        replace_s3_uris(data, client=client)
        client.generate_presigned_url.assert_not_called()
