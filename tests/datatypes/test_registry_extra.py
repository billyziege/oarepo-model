#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see https://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Additional tests for DataTypeRegistry and loader functions.

Covers:
- from_json: dict format and list format (with and without origin)
- from_yaml: dict format and list format (with and without origin)
- get_type: unknown type raises KeyError
- get_type: dict with neither type/properties/items raises ValueError
- add_types: invalid type value (not dict, not DataType subclass) raises TypeError
- add_types with DataType subclass
- registry.items() returns all registered types
- Duplicate type registration emits a warning (or silently overwrites)
"""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import pytest
import yaml

from oarepo_model.datatypes.registry import DataTypeRegistry, from_json, from_yaml


# ===========================================================================
# from_json
# ===========================================================================

class TestFromJson:
    """from_json must parse both dict and list formats."""

    def _write_json(self, data: object, *, dir: str) -> str:
        path = os.path.join(dir, "types.json")
        Path(path).write_text(json.dumps(data), encoding="utf-8")
        return path

    def test_dict_format_returns_dict(self, tmp_path):
        path = self._write_json(
            {"MyType": {"type": "keyword"}}, dir=str(tmp_path)
        )
        result = from_json(path)
        assert result == {"MyType": {"type": "keyword"}}

    def test_list_format_returns_dict_keyed_by_name(self, tmp_path):
        path = self._write_json(
            [{"name": "MyType", "type": "keyword"}], dir=str(tmp_path)
        )
        result = from_json(path)
        assert "MyType" in result
        # 'name' is popped, so it should not be in the value dict
        assert "name" not in result["MyType"]
        assert result["MyType"]["type"] == "keyword"

    def test_list_format_multiple_entries(self, tmp_path):
        path = self._write_json(
            [
                {"name": "TypeA", "type": "keyword"},
                {"name": "TypeB", "type": "fulltext"},
            ],
            dir=str(tmp_path),
        )
        result = from_json(path)
        assert set(result.keys()) == {"TypeA", "TypeB"}

    def test_origin_resolves_relative_path(self, tmp_path):
        """When origin is given, file_name is resolved relative to its parent dir."""
        origin_file = tmp_path / "subdir" / "origin.py"
        origin_file.parent.mkdir()
        origin_file.write_text("")

        types_file = tmp_path / "subdir" / "types.json"
        types_file.write_text(json.dumps({"T": {"type": "int"}}), encoding="utf-8")

        result = from_json("types.json", origin=str(origin_file))
        assert result == {"T": {"type": "int"}}


# ===========================================================================
# from_yaml
# ===========================================================================

class TestFromYaml:
    """from_yaml must parse both dict and list formats."""

    def test_dict_format_returns_dict(self, tmp_path):
        path = tmp_path / "types.yaml"
        path.write_text(yaml.dump({"MyType": {"type": "keyword"}}), encoding="utf-8")
        result = from_yaml(str(path))
        assert result == {"MyType": {"type": "keyword"}}

    def test_list_format_returns_dict_keyed_by_name(self, tmp_path):
        path = tmp_path / "types.yaml"
        path.write_text(
            yaml.dump([{"name": "MyType", "type": "keyword"}]),
            encoding="utf-8",
        )
        result = from_yaml(str(path))
        assert "MyType" in result
        assert "name" not in result["MyType"]
        assert result["MyType"]["type"] == "keyword"

    def test_list_format_multiple_entries(self, tmp_path):
        path = tmp_path / "types.yaml"
        path.write_text(
            yaml.dump([{"name": "A", "type": "keyword"}, {"name": "B", "type": "int"}]),
            encoding="utf-8",
        )
        result = from_yaml(str(path))
        assert set(result.keys()) == {"A", "B"}

    def test_origin_resolves_relative_path(self, tmp_path):
        origin_file = tmp_path / "pkg" / "__init__.py"
        origin_file.parent.mkdir()
        origin_file.write_text("")

        types_file = tmp_path / "pkg" / "types.yaml"
        types_file.write_text(yaml.dump({"Z": {"type": "boolean"}}), encoding="utf-8")

        result = from_yaml("types.yaml", origin=str(origin_file))
        assert result == {"Z": {"type": "boolean"}}


# ===========================================================================
# get_type error paths
# ===========================================================================

class TestGetTypeErrorPaths:
    """get_type must raise clear errors for unknown or ambiguous inputs."""

    def test_unknown_string_type_raises_key_error(self, datatype_registry):
        with pytest.raises(KeyError, match="not_a_real_type"):
            datatype_registry.get_type("not_a_real_type")

    def test_dict_without_type_or_properties_or_items_raises_value_error(self, datatype_registry):
        with pytest.raises(ValueError):
            datatype_registry.get_type({"something": "else"})

    def test_dict_with_type_key_resolves_correctly(self, datatype_registry):
        from oarepo_model.datatypes.strings import KeywordDataType
        dt = datatype_registry.get_type({"type": "keyword"})
        assert isinstance(dt, KeywordDataType)

    def test_dict_with_properties_key_resolves_to_object(self, datatype_registry):
        from oarepo_model.datatypes.collections import ObjectDataType
        dt = datatype_registry.get_type({"properties": {"x": {"type": "int"}}})
        assert isinstance(dt, ObjectDataType)

    def test_dict_with_items_key_resolves_to_array(self, datatype_registry):
        from oarepo_model.datatypes.collections import ArrayDataType
        dt = datatype_registry.get_type({"items": {"type": "int"}})
        assert isinstance(dt, ArrayDataType)


# ===========================================================================
# add_types error paths
# ===========================================================================

class TestAddTypesErrorPaths:
    """add_types must raise TypeError for values that are neither dicts nor DataType subclasses."""

    def test_add_types_with_invalid_value_raises_type_error(self, datatype_registry):
        with pytest.raises(TypeError):
            datatype_registry.add_types({"BadType": 42})

    def test_add_types_with_string_value_raises_type_error(self, datatype_registry):
        with pytest.raises(TypeError):
            datatype_registry.add_types({"BadType": "not_a_class"})

    def test_add_types_with_non_datatype_class_raises_type_error(self, datatype_registry):
        with pytest.raises(TypeError):
            datatype_registry.add_types({"BadType": int})

    def test_add_types_with_dict_registers_wrapped_datatype(self, datatype_registry):
        from oarepo_model.datatypes.wrapped import WrappedDataType
        datatype_registry.add_types({"CustomKw": {"type": "keyword"}})
        dt = datatype_registry.get_type("CustomKw")
        assert isinstance(dt, WrappedDataType)

    def test_add_types_with_datatype_subclass_registers_instance(self, datatype_registry):
        from oarepo_model.datatypes.base import DataType
        from oarepo_model.datatypes.strings import KeywordDataType

        datatype_registry.add_types({"MyKeyword": KeywordDataType})
        dt = datatype_registry.get_type("MyKeyword")
        assert isinstance(dt, KeywordDataType)


# ===========================================================================
# registry.items()
# ===========================================================================

class TestRegistryItems:
    """items() must expose all registered types as (name, DataType) pairs."""

    def test_items_contains_builtin_types(self, datatype_registry):
        names = {name for name, _ in datatype_registry.items()}
        for expected in ("keyword", "fulltext", "fulltext+keyword", "int", "float", "boolean"):
            assert expected in names, f"Expected {expected!r} in registry"

    def test_items_reflects_add_types(self, datatype_registry):
        datatype_registry.add_types({"UniqueTestType999": {"type": "keyword"}})
        names = {name for name, _ in datatype_registry.items()}
        assert "UniqueTestType999" in names


# ===========================================================================
# Duplicate registration
# ===========================================================================

class TestDuplicateRegistration:
    """Registering a type name twice must overwrite the old registration."""

    def test_duplicate_type_overwrites_silently(self, datatype_registry):
        from oarepo_model.datatypes.strings import FullTextDataType, KeywordDataType

        datatype_registry.add_types({"DupType": {"type": "keyword"}})
        datatype_registry.add_types({"DupType": {"type": "fulltext"}})
        # The second registration wins; the type should produce a text mapping.
        dt = datatype_registry.get_type("DupType")
        mapping = dt.create_mapping({"type": "DupType"})
        assert mapping["type"] == "text"
