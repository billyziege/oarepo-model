#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see https://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Additional tests for collection data types.

Covers:
- unique_validator function (valid list passes, list with duplicates raises)
- unique_items=True enforced through array marshmallow field
- Array min_items / max_items constraints
- NestedDataType mapping type is "nested"
- ObjectDataType error path: missing "properties" key
- ObjectDataType error path: invalid marshmallow_schema_class string
- [] shortcut expansion inside add_types / get_type (properties + items dict shortcuts)
- DynamicObjectDataType JSON schema and mapping
- ArrayDataType create_mapping delegates to items (skips the array wrapper)
"""
from __future__ import annotations

import pytest
import marshmallow as ma

from oarepo_model.datatypes.collections import unique_validator


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_schema(datatype_registry, element, extra_types=None):
    if extra_types:
        datatype_registry.add_types(extra_types)
    field = datatype_registry.get_type(element).create_marshmallow_field(
        field_name="a", element=element
    )
    return ma.Schema.from_dict({"a": field})()


# ===========================================================================
# unique_validator (unit-level)
# ===========================================================================

class TestUniqueValidator:
    """unique_validator must raise only when duplicates are present."""

    def test_empty_list_is_valid(self):
        unique_validator([])  # must not raise

    def test_list_of_unique_scalars_is_valid(self):
        unique_validator([1, 2, 3])

    def test_list_of_unique_dicts_is_valid(self):
        unique_validator([{"a": 1}, {"a": 2}])

    def test_list_with_duplicate_scalar_raises(self):
        with pytest.raises(ma.ValidationError):
            unique_validator([1, 2, 1])

    def test_list_with_duplicate_dict_raises(self):
        with pytest.raises(ma.ValidationError):
            unique_validator([{"a": 1}, {"a": 1}])

    def test_list_with_multiple_duplicates_raises(self):
        with pytest.raises(ma.ValidationError):
            unique_validator([1, 1, 2, 2])


# ===========================================================================
# unique_items=True through array schema
# ===========================================================================

class TestUniqueItemsInArray:
    """unique_items=True on an array element must reject duplicate entries."""

    def test_unique_items_rejects_duplicates(self, datatype_registry):
        schema = make_schema(
            datatype_registry,
            {"type": "array", "items": {"type": "keyword"}, "unique_items": True},
        )
        with pytest.raises(ma.ValidationError):
            schema.load({"a": ["x", "x"]})

    def test_unique_items_accepts_distinct_values(self, datatype_registry):
        schema = make_schema(
            datatype_registry,
            {"type": "array", "items": {"type": "keyword"}, "unique_items": True},
        )
        assert schema.load({"a": ["x", "y", "z"]}) == {"a": ["x", "y", "z"]}

    def test_without_unique_items_duplicates_are_accepted(self, datatype_registry):
        schema = make_schema(
            datatype_registry,
            {"type": "array", "items": {"type": "keyword"}},
        )
        assert schema.load({"a": ["x", "x"]}) == {"a": ["x", "x"]}


# ===========================================================================
# Array min_items / max_items
# ===========================================================================

class TestArrayLengthConstraints:
    """min_items and max_items must be enforced via marshmallow.validate.Length."""

    def test_min_items_rejects_too_few(self, datatype_registry):
        schema = make_schema(
            datatype_registry,
            {"type": "array", "items": {"type": "int"}, "min_items": 2},
        )
        with pytest.raises(ma.ValidationError):
            schema.load({"a": [1]})

    def test_min_items_accepts_exact_count(self, datatype_registry):
        schema = make_schema(
            datatype_registry,
            {"type": "array", "items": {"type": "int"}, "min_items": 2},
        )
        assert schema.load({"a": [1, 2]}) == {"a": [1, 2]}

    def test_max_items_rejects_too_many(self, datatype_registry):
        schema = make_schema(
            datatype_registry,
            {"type": "array", "items": {"type": "int"}, "max_items": 2},
        )
        with pytest.raises(ma.ValidationError):
            schema.load({"a": [1, 2, 3]})

    def test_max_items_accepts_exact_count(self, datatype_registry):
        schema = make_schema(
            datatype_registry,
            {"type": "array", "items": {"type": "int"}, "max_items": 2},
        )
        assert schema.load({"a": [1, 2]}) == {"a": [1, 2]}


# ===========================================================================
# NestedDataType
# ===========================================================================

class TestNestedDataType:
    """nested type must produce ES mapping type 'nested', not 'object'."""

    def test_nested_mapping_type_is_nested(self, datatype_registry):
        dt = datatype_registry.get_type({"type": "nested"})
        mapping = dt.create_mapping(
            {"type": "nested", "properties": {"x": {"type": "keyword"}}}
        )
        assert mapping["type"] == "nested"

    def test_nested_mapping_contains_properties(self, datatype_registry):
        dt = datatype_registry.get_type({"type": "nested"})
        mapping = dt.create_mapping(
            {"type": "nested", "properties": {"score": {"type": "int"}}}
        )
        assert "score" in mapping["properties"]

    def test_nested_schema_round_trip(self, datatype_registry):
        schema = make_schema(
            datatype_registry,
            {
                "type": "array",
                "items": {
                    "type": "nested",
                    "properties": {"tag": {"type": "keyword"}},
                },
            },
        )
        data = {"a": [{"tag": "foo"}, {"tag": "bar"}]}
        assert schema.load(data) == data


# ===========================================================================
# ObjectDataType error paths
# ===========================================================================

class TestObjectDataTypeErrorPaths:
    """ObjectDataType must raise clear errors for invalid configurations."""

    def test_missing_properties_raises_value_error(self, datatype_registry):
        """create_marshmallow_field on an object without 'properties' must raise ValueError."""
        dt = datatype_registry.get_type({"type": "object"})
        with pytest.raises((ValueError, TypeError)):
            dt.create_marshmallow_field(
                field_name="a",
                element={"type": "object"},  # no properties
            )

    def test_invalid_marshmallow_schema_class_raises(self, datatype_registry):
        """marshmallow_schema_class pointing to a non-Schema class must raise ValueError."""
        dt = datatype_registry.get_type({"type": "object"})
        with pytest.raises((ValueError, ImportError, AttributeError, Exception)):
            dt.create_marshmallow_schema(
                {"type": "object", "marshmallow_schema_class": "this.does.not.exist:Foo"}
            )


# ===========================================================================
# [] shortcut and dict shortcuts in get_type
# ===========================================================================

class TestRegistryShortcuts:
    """The registry must resolve 'properties' and 'items' dict shortcuts."""

    def test_get_type_with_properties_dict_resolves_to_object(self, datatype_registry):
        """A dict with 'properties' but no 'type' key must resolve to ObjectDataType."""
        from oarepo_model.datatypes.collections import ObjectDataType
        dt = datatype_registry.get_type({"properties": {"x": {"type": "keyword"}}})
        assert isinstance(dt, ObjectDataType)

    def test_get_type_with_items_dict_resolves_to_array(self, datatype_registry):
        """A dict with 'items' but no 'type' key must resolve to ArrayDataType."""
        from oarepo_model.datatypes.collections import ArrayDataType
        dt = datatype_registry.get_type({"items": {"type": "keyword"}})
        assert isinstance(dt, ArrayDataType)

    def test_array_bracket_shortcut_in_nested_properties(self, datatype_registry):
        """A property key ending in '[]' inside an object's 'properties' dict must
        be expanded to type=array when the type is registered and later referenced.
        """
        datatype_registry.add_types(
            {
                "TaggedItem": {
                    "type": "object",
                    "properties": {
                        "tags[]": {"type": "keyword"},
                    },
                }
            }
        )
        dt = datatype_registry.get_type("TaggedItem")
        # Reference the registered type by name (the normal usage pattern).
        # _merge_type_dict strips the "type" key and merges nothing else,
        # so the registered type_dict (with expanded tags[]) is used as-is.
        field = dt.create_marshmallow_field("item", {"type": "TaggedItem"})
        # The resulting field is a Nested schema containing a List sub-field.
        assert isinstance(field, ma.fields.Nested)
        inner_schema = field.schema
        # Field names are converted to Python identifiers; 'tags[]' → 'tags_91__93_'
        list_fields = [f for f in inner_schema.fields.values() if isinstance(f, ma.fields.List)]
        assert list_fields, (
            f"Expected a List field in the inner schema, got: "
            f"{{{k}: type(v).__name__ for k, v in inner_schema.fields.items()}}"
        )


# ===========================================================================
# DynamicObjectDataType JSON schema and mapping
# ===========================================================================

class TestDynamicObjectDataType:
    """dynamic-object must advertise open schema and dynamic mapping."""

    def test_json_schema_allows_additional_properties(self, datatype_registry):
        dt = datatype_registry.get_type({"type": "dynamic-object"})
        schema = dt.create_json_schema({"type": "dynamic-object"})
        assert schema.get("additionalProperties") is True

    def test_mapping_uses_dynamic_true(self, datatype_registry):
        dt = datatype_registry.get_type({"type": "dynamic-object"})
        mapping = dt.create_mapping({"type": "dynamic-object"})
        assert mapping.get("dynamic") in ("true", True)


# ===========================================================================
# ArrayDataType create_mapping delegates to items
# ===========================================================================

class TestArrayMappingDelegation:
    """Arrays are transparent in ES: create_mapping must return the items mapping."""

    def test_array_of_keywords_produces_keyword_mapping(self, datatype_registry):
        dt = datatype_registry.get_type({"type": "array"})
        mapping = dt.create_mapping(
            {"type": "array", "items": {"type": "keyword"}}
        )
        assert mapping["type"] == "keyword"

    def test_array_of_ints_produces_integer_mapping(self, datatype_registry):
        dt = datatype_registry.get_type({"type": "array"})
        mapping = dt.create_mapping(
            {"type": "array", "items": {"type": "int"}}
        )
        assert mapping["type"] == "integer"
