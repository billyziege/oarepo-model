#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see https://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Tests for multilingual data types.

Covers:
- multilingual_validator (unique language codes pass; duplicate codes raise)
- MultilingualDataType: load and dump round-trip, duplicate language rejection
- I18nDictDataType: field type, load/dump of language-keyed dicts, JSON schema, mapping
"""
from __future__ import annotations

import pytest
import marshmallow as ma

from oarepo_model.datatypes.multilingual import multilingual_validator


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def make_schema(datatype_registry, element):
    field = datatype_registry.get_type(element).create_marshmallow_field(
        field_name="a", element=element
    )
    return ma.Schema.from_dict({"a": field})()


# ===========================================================================
# multilingual_validator (unit tests)
# ===========================================================================

class TestMultilingualValidator:
    """multilingual_validator must reject lists that contain duplicate language codes."""

    def _entry(self, lang_id: str, value: str = "text") -> dict:
        return {"lang": {"id": lang_id}, "value": value}

    def test_empty_list_is_valid(self):
        multilingual_validator([])  # must not raise

    def test_single_entry_is_valid(self):
        multilingual_validator([self._entry("en")])

    def test_two_distinct_languages_are_valid(self):
        multilingual_validator([self._entry("en"), self._entry("fi")])

    def test_many_distinct_languages_are_valid(self):
        multilingual_validator([self._entry(lang) for lang in ["en", "fi", "de", "fr", "es"]])

    def test_duplicate_language_raises(self):
        with pytest.raises(ma.ValidationError, match="en"):
            multilingual_validator([self._entry("en"), self._entry("en")])

    def test_duplicate_among_many_raises(self):
        with pytest.raises(ma.ValidationError):
            multilingual_validator([
                self._entry("en"),
                self._entry("fi"),
                self._entry("en"),  # duplicate
            ])

    def test_two_different_duplicates_raises(self):
        """Even a single duplicate triggers the error."""
        with pytest.raises(ma.ValidationError):
            multilingual_validator([self._entry("de"), self._entry("de")])


# ===========================================================================
# MultilingualDataType — integration via the registry
# ===========================================================================

class TestMultilingualDataType:
    """multilingual type (registered via entry-points) must validate language uniqueness."""

    @pytest.fixture
    def ml_schema(self, datatype_registry):
        field = datatype_registry.get_type({"type": "multilingual"}).create_marshmallow_field(
            "titles", {"type": "multilingual"}
        )
        return ma.Schema.from_dict({"titles": field})()

    def test_single_language_entry_loads(self, ml_schema):
        data = {"titles": [{"lang": {"id": "en"}, "value": "Hello"}]}
        assert ml_schema.load(data) == data

    def test_multiple_distinct_languages_load(self, ml_schema):
        data = {"titles": [
            {"lang": {"id": "en"}, "value": "Hello"},
            {"lang": {"id": "fi"}, "value": "Hei"},
        ]}
        assert ml_schema.load(data) == data

    def test_duplicate_language_raises_validation_error(self, ml_schema):
        with pytest.raises(ma.ValidationError) as exc_info:
            ml_schema.load({"titles": [
                {"lang": {"id": "en"}, "value": "Hello"},
                {"lang": {"id": "en"}, "value": "World"},
            ]})
        assert "en" in str(exc_info.value.messages)

    def test_empty_list_is_accepted(self, ml_schema):
        assert ml_schema.load({"titles": []}) == {"titles": []}

    def test_dump_round_trip(self, ml_schema):
        original = {"titles": [
            {"lang": {"id": "en"}, "value": "Hello"},
            {"lang": {"id": "fi"}, "value": "Hei"},
        ]}
        loaded = ml_schema.load(original)
        dumped = ml_schema.dump(loaded)
        assert dumped == original


# ===========================================================================
# I18nDictDataType
# ===========================================================================

class TestI18nDictDataType:
    """i18ndict type represents a simple {lang_code: text} dictionary."""

    @pytest.fixture
    def i18n_schema(self, datatype_registry):
        return make_schema(datatype_registry, {"type": "i18ndict"})

    def test_load_language_keyed_dict(self, i18n_schema):
        data = {"a": {"en": "Hello", "fi": "Hei"}}
        assert i18n_schema.load(data) == data

    def test_load_single_language(self, i18n_schema):
        data = {"a": {"en": "Only English"}}
        assert i18n_schema.load(data) == data

    def test_dump_round_trip(self, i18n_schema):
        original = {"a": {"en": "Hello", "de": "Hallo", "fr": "Bonjour"}}
        assert i18n_schema.dump(i18n_schema.load(original)) == original

    def test_json_schema_uses_object_with_string_values(self, datatype_registry):
        dt = datatype_registry.get_type({"type": "i18ndict"})
        schema = dt.create_json_schema({"type": "i18ndict"})
        assert schema["type"] == "object"
        assert schema.get("additionalProperties") == {"type": "string"}

    def test_mapping_uses_dynamic_true(self, datatype_registry):
        dt = datatype_registry.get_type({"type": "i18ndict"})
        mapping = dt.create_mapping({"type": "i18ndict"})
        assert mapping.get("dynamic") in ("true", True)
        assert mapping.get("type") == "object"
