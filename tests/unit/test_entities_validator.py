from __future__ import annotations

import pytest

from logforge.entities import validator


def test_validate_bundle_detects_duplicates():
    data = {
        "organization": {"name": "Acme", "domain": "acme.com"},
        "users": [
            {"username": "alice", "email": "alice@acme.com"},
            {"username": "alice", "email": "alice2@acme.com"},
        ],
    }
    with pytest.raises(validator.EntityValidationError):
        validator.validate_bundle(data)


def test_validate_entity_payload_allows_single_user():
    payload = {"username": "alice", "email": "alice@acme.com"}
    validated = validator.validate_entity_payload("users", payload)
    assert validated["username"] == "alice"


def test_validate_entity_payload_rejects_bad_mac():
    payload = {"hostname": "ws1", "ip_address": "192.168.1.2", "mac_address": "bad-mac"}
    with pytest.raises(validator.EntityValidationError):
        validator.validate_entity_payload("devices", payload)
