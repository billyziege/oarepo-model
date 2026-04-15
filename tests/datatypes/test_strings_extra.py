#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see https://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Additional tests for string data types.

Covers:
- enum validation on keyword / fulltext / fulltext+keyword
- pattern validation
- required + implicit min_length=1 behaviour
- field options: dump_only, load_only, allow_none
- facet generation: fulltext → no facet; keyword → facet; fulltext+keyword → .keyword suffix
- mapping types for all three string types
- JSON schema type for all three string types
"""
from __future__ import annotations

import pytest
import marshmallow as ma


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_schema(datatype_registry, element):
    field = datatype_registry.get_type(element).create_marshmallow_field(
        field_name="a", element=element
    )
    return ma.Schema.from_dict({"a": field})()


# ===========================================================================
# Enum validation
# ===========================================================================

class TestEnumValidation:
    """enum constraint must limit accepted values for string types."""

    @pytest.mark.parametrize("type_name", ["keyword", "fulltext", "fulltext+keyword"])
    def test_enum_accepts_valid_value(self, datatype_registry, type_name):
        schema = make_schema(
            datatype_registry,
            {"type": type_name, "enum": ["alpha", "beta", "gamma"]},
        )
        assert schema.load({"a": "alpha"}) == {"a": "alpha"}

    @pytest.mark.parametrize("type_name", ["keyword", "fulltext", "fulltext+keyword"])
    def test_enum_rejects_invalid_value(self, datatype_registry, type_name):
        schema = make_schema(
            datatype_registry,
            {"type": type_name, "enum": ["alpha", "beta", "gamma"]},
        )
        with pytest.raises(ma.ValidationError):
            schema.load({"a": "delta"})

    def test_enum_all_values_accepted(self, datatype_registry):
        """Every value in the enum list must be accepted."""
        schema = make_schema(
            datatype_registry,
            {"type": "keyword", "enum": ["x", "y", "z"]},
        )
        for val in ["x", "y", "z"]:
            assert schema.load({"a": val}) == {"a": val}


# ===========================================================================
# Pattern validation
# ===========================================================================

class TestPatternValidation:
    """pattern constraint must limit accepted values for string types."""

    def test_pattern_accepts_matching_value(self, datatype_registry):
        schema = make_schema(
            datatype_registry,
            {"type": "keyword", "pattern": r"^\d{4}$"},
        )
        assert schema.load({"a": "2025"}) == {"a": "2025"}

    def test_pattern_rejects_non_matching_value(self, datatype_registry):
        schema = make_schema(
            datatype_registry,
            {"type": "keyword", "pattern": r"^\d{4}$"},
        )
        with pytest.raises(ma.ValidationError):
            schema.load({"a": "not-four-digits"})

    def test_pattern_and_enum_can_coexist(self, datatype_registry):
        """enum and pattern validators are both applied."""
        schema = make_schema(
            datatype_registry,
            {"type": "keyword", "enum": ["abc", "def"], "pattern": r"^[a-z]+$"},
        )
        assert schema.load({"a": "abc"}) == {"a": "abc"}
        with pytest.raises(ma.ValidationError):
            # passes pattern but not enum
            schema.load({"a": "xyz"})


# ===========================================================================
# required + implicit min_length
# ===========================================================================

class TestRequiredImpliesMinLength:
    """When required=True and no explicit min_length, the field must reject
    the empty string — because a min_length=1 validator is injected.
    """

    def test_required_rejects_empty_string(self, datatype_registry):
        schema = make_schema(
            datatype_registry,
            {"type": "keyword", "required": True},
        )
        with pytest.raises(ma.ValidationError):
            schema.load({"a": ""})

    def test_required_accepts_non_empty_string(self, datatype_registry):
        schema = make_schema(
            datatype_registry,
            {"type": "keyword", "required": True},
        )
        assert schema.load({"a": "ok"}) == {"a": "ok"}

    def test_explicit_min_length_zero_with_required_allows_empty(self, datatype_registry):
        """If min_length is explicitly set, required does NOT add its own min_length=1."""
        schema = make_schema(
            datatype_registry,
            {"type": "keyword", "required": True, "min_length": 0},
        )
        # min_length=0 means empty string is valid
        assert schema.load({"a": ""}) == {"a": ""}

    def test_max_length_alone_does_not_imply_required(self, datatype_registry):
        """max_length without required must allow empty strings."""
        schema = make_schema(
            datatype_registry,
            {"type": "keyword", "max_length": 10},
        )
        assert schema.load({"a": ""}) == {"a": ""}


# ===========================================================================
# Field options: dump_only / load_only / allow_none
# ===========================================================================

class TestFieldOptions:
    """dump_only, load_only, and allow_none must be forwarded to the marshmallow field."""

    def test_dump_only_field_is_ignored_on_load(self, datatype_registry):
        field = datatype_registry.get_type(
            {"type": "keyword", "dump_only": True}
        ).create_marshmallow_field(field_name="a", element={"type": "keyword", "dump_only": True})
        assert field.dump_only is True

    def test_load_only_field_is_ignored_on_dump(self, datatype_registry):
        field = datatype_registry.get_type(
            {"type": "keyword", "load_only": True}
        ).create_marshmallow_field(field_name="a", element={"type": "keyword", "load_only": True})
        assert field.load_only is True

    def test_allow_none_field_accepts_null(self, datatype_registry):
        schema = make_schema(
            datatype_registry,
            {"type": "keyword", "allow_none": True},
        )
        assert schema.load({"a": None}) == {"a": None}

    def test_disallow_none_by_default(self, datatype_registry):
        schema = make_schema(datatype_registry, {"type": "keyword"})
        with pytest.raises(ma.ValidationError):
            schema.load({"a": None})


# ===========================================================================
# Facet generation
# ===========================================================================

class TestStringFacets:
    """Facet behaviour differs across string types."""

    def test_fulltext_produces_no_facet(self, datatype_registry):
        dt = datatype_registry.get_type({"type": "fulltext"})
        facets = {}
        result = dt.get_facet("metadata.title", {"type": "fulltext"}, [], facets)
        assert "metadata.title" not in result, (
            "fulltext must not produce a facet (full-text fields are not aggregatable)"
        )

    def test_keyword_produces_facet(self, datatype_registry):
        dt = datatype_registry.get_type({"type": "keyword"})
        facets = {}
        result = dt.get_facet("metadata.status", {"type": "keyword"}, [], facets)
        assert "metadata.status" in result, "keyword must produce a facet"

    def test_fulltext_keyword_facet_uses_keyword_suffix(self, datatype_registry):
        """The facet entry for fulltext+keyword must reference the .keyword sub-field
        in its field descriptor, even though the facet dict key keeps the original path.
        """
        dt = datatype_registry.get_type({"type": "fulltext+keyword"})
        facets = {}
        result = dt.get_facet("metadata.title", {"type": "fulltext+keyword"}, [], facets)
        assert "metadata.title" in result
        # The TermsFacet 'field' value must point to the .keyword sub-field
        facet_def = result["metadata.title"]
        field_values = [
            entry.get("field", "")
            for entry in (facet_def if isinstance(facet_def, list) else [facet_def])
        ]
        assert any(".keyword" in f for f in field_values), (
            f"Expected .keyword in facet field, got: {field_values}"
        )

    def test_fulltext_keyword_facet_path_structure(self, datatype_registry):
        """The facet field for fulltext+keyword must be 'original_path.keyword'."""
        dt = datatype_registry.get_type({"type": "fulltext+keyword"})
        facets = {}
        result = dt.get_facet("metadata.title", {"type": "fulltext+keyword"}, [], facets)
        assert "metadata.title" in result
        facet_def = result["metadata.title"]
        entries = facet_def if isinstance(facet_def, list) else [facet_def]
        fields = [e.get("field", "") for e in entries]
        assert "metadata.title.keyword" in fields


# ===========================================================================
# Mapping types
# ===========================================================================

class TestStringMappings:
    """Each string type must produce its correct Elasticsearch mapping."""

    def test_keyword_mapping_type(self, datatype_registry):
        dt = datatype_registry.get_type({"type": "keyword"})
        mapping = dt.create_mapping({"type": "keyword"})
        assert mapping["type"] == "keyword"

    def test_fulltext_mapping_type(self, datatype_registry):
        dt = datatype_registry.get_type({"type": "fulltext"})
        mapping = dt.create_mapping({"type": "fulltext"})
        assert mapping["type"] == "text"

    def test_fulltext_keyword_mapping_has_keyword_subfield(self, datatype_registry):
        dt = datatype_registry.get_type({"type": "fulltext+keyword"})
        mapping = dt.create_mapping({"type": "fulltext+keyword"})
        assert mapping["type"] == "text"
        assert mapping["fields"]["keyword"]["type"] == "keyword"

    def test_keyword_json_schema_type_is_string(self, datatype_registry):
        dt = datatype_registry.get_type({"type": "keyword"})
        schema = dt.create_json_schema({"type": "keyword"})
        assert schema["type"] == "string"

    def test_fulltext_json_schema_type_is_string(self, datatype_registry):
        dt = datatype_registry.get_type({"type": "fulltext"})
        schema = dt.create_json_schema({"type": "fulltext"})
        assert schema["type"] == "string"
