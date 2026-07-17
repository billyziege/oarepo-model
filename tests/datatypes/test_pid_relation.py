#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see https://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Tests for the pid-relation bug fixes.

Bug 1 — pid-relation: build failure caused by eager import of record_cls at model
    construction time (relations.py _pid_field / add_pid_relation.py apply).

Bug 2 — pid-relation: string keys default to {type: keyword} in the generated
    mapping. If a key resolves to a vocabulary term in the target model the
    denormalised document stores {id: "..."} — an object — which causes
    mapper_parsing_exception. vocab_keys declares such keys so they are mapped
    as {type: object, properties: {id: {type: keyword}}}.
"""
from __future__ import annotations

import pytest


class TestPidRelationLazyImport:
    """_pid_field() must return a callable rather than resolving the import
    immediately, so that a model referencing another model can be constructed
    without a circular-import or missing-module error at import time.
    """

    def test_pid_field_returns_callable_for_record_cls(self, datatype_registry):
        """_pid_field() must return a callable even when the module does not exist."""
        element = {
            "type": "pid-relation",
            "keys": ["id"],
            "record_cls": "this.module.does.not.exist:SomeRecord",
        }
        dt = datatype_registry.get_type(element)
        result = dt._pid_field(element, [])
        assert callable(result), (
            "_pid_field() should return a callable (lazy resolver), "
            "not raise ImportError at call time"
        )

    def test_pid_field_returns_callable_for_pid_field(self, datatype_registry):
        """_pid_field() must return a callable when pid_field string is given."""
        element = {
            "type": "pid-relation",
            "keys": ["id"],
            "pid_field": "this.module.does.not.exist:get_pid",
        }
        dt = datatype_registry.get_type(element)
        result = dt._pid_field(element, [])
        assert callable(result), (
            "_pid_field() should return a callable for pid_field strings too"
        )

    def test_pid_field_callable_raises_on_bad_record_cls(self, datatype_registry):
        """The callable returned by _pid_field() must raise ValueError when
        the record_cls cannot be imported — but only when the callable is invoked,
        not at _pid_field() call time.
        """
        element = {
            "type": "pid-relation",
            "keys": ["id"],
            "record_cls": "this.module.does.not.exist:SomeRecord",
        }
        dt = datatype_registry.get_type(element)
        resolver = dt._pid_field(element, [])
        with pytest.raises(Exception):
            # The import failure must surface here, not during _pid_field()
            resolver()

    def test_pid_field_raises_without_pid_field_or_record_cls(self, datatype_registry):
        """_pid_field() must raise ValueError immediately when neither
        pid_field nor record_cls is provided — there is nothing to defer.
        """
        element = {
            "type": "pid-relation",
            "keys": ["id"],
        }
        dt = datatype_registry.get_type(element)
        with pytest.raises(ValueError, match="Either 'pid_field' or 'record_cls'"):
            dt._pid_field(element, [])

    def test_create_relations_does_not_import_at_call_time(self, datatype_registry):
        """create_relations() must complete without raising even when record_cls
        points to a non-existent module, because the import is deferred.
        """
        element = {
            "type": "pid-relation",
            "keys": ["id", "metadata.title"],
            "record_cls": "this.module.does.not.exist:SomeRecord",
        }
        dt = datatype_registry.get_type(element)
        # This must not raise — the import happens later in AddPIDRelation.apply()
        customizations = dt.create_relations(element, [("my_field", element)])
        assert len(customizations) == 1

    def test_add_pid_relation_stores_callable(self, datatype_registry):
        """AddPIDRelation must store the callable so that apply() can resolve it."""
        from oarepo_model.customizations.high_level.add_pid_relation import AddPIDRelation

        sentinel = object()  # stand-in for a PIDFieldContext

        def lazy_resolver():
            return sentinel

        relation = AddPIDRelation(
            name="my_field",
            path=["my_field"],
            keys=["id"],
            pid_field=lazy_resolver,
        )
        assert relation.pid_field is lazy_resolver, (
            "AddPIDRelation should store the callable unchanged"
        )

    def test_add_pid_relation_accepts_direct_value_for_backward_compat(self, datatype_registry):
        """AddPIDRelation must also accept a pre-resolved PIDFieldContext value
        (not callable) for backward compatibility.
        """
        from oarepo_model.customizations.high_level.add_pid_relation import AddPIDRelation

        sentinel = object()
        relation = AddPIDRelation(
            name="my_field",
            path=["my_field"],
            keys=["id"],
            pid_field=sentinel,
        )
        assert relation.pid_field is sentinel


class TestPidRelationVocabKeyMapping:
    """vocab_keys must produce object mappings for vocabulary-typed fields.

    Without vocab_keys, all string keys default to {"type": "keyword"}.
    Vocabulary terms are stored in OpenSearch as {"id": "..."} (an object),
    so a scalar keyword mapping causes mapper_parsing_exception at index time.
    """

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
        # The activity_type key should produce an object mapping, not a scalar keyword
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
        custom_mapping = {"type": "object", "properties": {"id": {"type": "keyword"}, "title": {"type": "object"}}}
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
