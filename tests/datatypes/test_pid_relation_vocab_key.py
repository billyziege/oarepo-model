#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see https://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Tests for pid-relation vocab_keys mapping fix.

Bug: string keys in a pid-relation default to {type: keyword} in the generated
OpenSearch mapping. If a key resolves to a vocabulary term in the target model
the denormalised document stores {id: "..."} — an object — which causes
mapper_parsing_exception at index time.

Fix: add vocab_keys list to the pid-relation element. Keys listed there are
mapped as {type: object, properties: {id: {type: keyword}}} instead of the
scalar keyword default.
"""

from __future__ import annotations

import pytest


class TestPidRelationVocabKeyMapping:
    """vocab_keys must produce object mappings for vocabulary-typed fields."""

    def _get_properties(self, datatype_registry, element: dict) -> dict:
        dt = datatype_registry.get_type(element)
        return dt._get_properties(element)

    def test_string_key_defaults_to_keyword(self, datatype_registry):
        """Without vocab_keys, a plain string key produces {type: keyword}."""
        element = {
            "type": "pid-relation",
            "keys": ["id", "metadata.title"],
            "pid_field": "invenio_pidstore.models:PersistentIdentifier.pid",
        }
        props = self._get_properties(datatype_registry, element)
        assert props["id"]["type"] == "keyword"

    def test_vocab_key_produces_object_mapping(self, datatype_registry):
        """A key listed in vocab_keys must emit the vocabulary term object mapping.

        Vocabulary terms are stored as {"id": "..."} in the OpenSearch document.
        The correct mapping is {type: object, properties: {id: {type: keyword}}}.
        A scalar keyword mapping causes mapper_parsing_exception at index time.
        """
        element = {
            "type": "pid-relation",
            "keys": ["id", "metadata.activity_type"],
            "vocab_keys": ["metadata.activity_type"],
            "pid_field": "invenio_pidstore.models:PersistentIdentifier.pid",
        }
        props = self._get_properties(datatype_registry, element)
        activity_type_mapping = props.get("metadata", {}).get("properties", {}).get("activity_type")
        assert activity_type_mapping is not None, "activity_type missing from properties"
        assert activity_type_mapping.get("type") == "object", (
            f"vocab_key should be mapped as object, got {activity_type_mapping!r}. "
            "Vocabulary terms are stored as {{id: ...}} at index time; scalar keyword "
            "causes mapper_parsing_exception."
        )
        assert "id" in activity_type_mapping.get("properties", {}), (
            "Vocabulary term object mapping must include 'id' sub-field"
        )

    def test_non_vocab_key_unchanged_when_vocab_keys_present(self, datatype_registry):
        """Keys not in vocab_keys remain as keyword even when vocab_keys is set."""
        element = {
            "type": "pid-relation",
            "keys": ["id", "metadata.title", "metadata.activity_type"],
            "vocab_keys": ["metadata.activity_type"],
            "pid_field": "invenio_pidstore.models:PersistentIdentifier.pid",
        }
        props = self._get_properties(datatype_registry, element)
        title_mapping = props.get("metadata", {}).get("properties", {}).get("title")
        assert title_mapping is not None
        assert title_mapping.get("type") == "keyword", (
            f"Non-vocab key should remain keyword, got {title_mapping!r}"
        )

    def test_dict_form_still_works_for_custom_overrides(self, datatype_registry):
        """Explicit dict form in keys overrides the default regardless of vocab_keys."""
        custom_mapping = {
            "type": "object",
            "properties": {"id": {"type": "keyword"}, "title": {"type": "object"}},
        }
        element = {
            "type": "pid-relation",
            "keys": [
                "id",
                {"metadata.activity_type": custom_mapping},
            ],
            "pid_field": "invenio_pidstore.models:PersistentIdentifier.pid",
        }
        props = self._get_properties(datatype_registry, element)
        activity_type_mapping = props.get("metadata", {}).get("properties", {}).get("activity_type")
        assert activity_type_mapping == custom_mapping

    def test_empty_vocab_keys_behaves_as_no_vocab_keys(self, datatype_registry):
        """An empty vocab_keys list must not change any key mappings."""
        element = {
            "type": "pid-relation",
            "keys": ["id", "metadata.title"],
            "vocab_keys": [],
            "pid_field": "invenio_pidstore.models:PersistentIdentifier.pid",
        }
        props = self._get_properties(datatype_registry, element)
        title_mapping = props.get("metadata", {}).get("properties", {}).get("title")
        assert title_mapping is not None
        assert title_mapping.get("type") == "keyword"
