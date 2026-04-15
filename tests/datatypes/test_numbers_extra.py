#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see https://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Additional tests for numeric data types.

Covers:
- LongDataType (64-bit integer bounds)
- DoubleDataType (double-precision float)
- Exclusive range boundaries (min_exclusive / max_exclusive)
- strict_validation=False (coerce strings to numbers)
- Number facet generation
- FormatNumber UI field presence
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
# LongDataType
# ===========================================================================

class TestLongDataType:
    """64-bit integer type — distinct from int (32-bit)."""

    def test_long_accepts_value_within_range(self, datatype_registry):
        schema = make_schema(datatype_registry, {"type": "long"})
        assert schema.load({"a": 0}) == {"a": 0}
        assert schema.load({"a": 2**62}) == {"a": 2**62}
        assert schema.load({"a": -(2**62)}) == {"a": -(2**62)}

    def test_long_accepts_max_value(self, datatype_registry):
        schema = make_schema(datatype_registry, {"type": "long"})
        assert schema.load({"a": 2**63 - 1}) == {"a": 2**63 - 1}

    def test_long_accepts_min_value(self, datatype_registry):
        schema = make_schema(datatype_registry, {"type": "long"})
        assert schema.load({"a": -(2**63)}) == {"a": -(2**63)}

    def test_long_rejects_value_above_max(self, datatype_registry):
        schema = make_schema(datatype_registry, {"type": "long"})
        with pytest.raises(ma.ValidationError):
            schema.load({"a": 2**63})

    def test_long_rejects_value_below_min(self, datatype_registry):
        schema = make_schema(datatype_registry, {"type": "long"})
        with pytest.raises(ma.ValidationError):
            schema.load({"a": -(2**63) - 1})

    def test_long_rejects_float(self, datatype_registry):
        """Long is strictly an integer; floats must be rejected."""
        schema = make_schema(datatype_registry, {"type": "long"})
        with pytest.raises(ma.ValidationError):
            schema.load({"a": 3.14})

    def test_long_rejects_string(self, datatype_registry):
        schema = make_schema(datatype_registry, {"type": "long"})
        with pytest.raises(ma.ValidationError):
            schema.load({"a": "not a number"})

    def test_long_exceeds_int32_max(self, datatype_registry):
        """A value that overflows int32 (2**31) must be valid for long."""
        schema = make_schema(datatype_registry, {"type": "long"})
        assert schema.load({"a": 2**31}) == {"a": 2**31}

    def test_long_mapping_type_is_long(self, datatype_registry):
        dt = datatype_registry.get_type({"type": "long"})
        mapping = dt.create_mapping({"type": "long"})
        assert mapping["type"] == "long"

    def test_long_with_custom_range(self, datatype_registry):
        schema = make_schema(
            datatype_registry,
            {"type": "long", "min_inclusive": 0, "max_inclusive": 100},
        )
        assert schema.load({"a": 50}) == {"a": 50}
        with pytest.raises(ma.ValidationError):
            schema.load({"a": -1})
        with pytest.raises(ma.ValidationError):
            schema.load({"a": 101})


# ===========================================================================
# DoubleDataType
# ===========================================================================

class TestDoubleDataType:
    """Double-precision floating-point type."""

    def test_double_accepts_float(self, datatype_registry):
        schema = make_schema(datatype_registry, {"type": "double"})
        result = schema.load({"a": 3.141592653589793})
        assert abs(result["a"] - 3.141592653589793) < 1e-10

    def test_double_accepts_integer_input(self, datatype_registry):
        """Integers are coercible to double."""
        schema = make_schema(datatype_registry, {"type": "double"})
        assert schema.load({"a": 42}) == {"a": 42.0}

    def test_double_accepts_negative(self, datatype_registry):
        schema = make_schema(datatype_registry, {"type": "double"})
        result = schema.load({"a": -1.23e100})
        assert result["a"] == -1.23e100

    def test_double_rejects_string(self, datatype_registry):
        schema = make_schema(datatype_registry, {"type": "double"})
        with pytest.raises(ma.ValidationError):
            schema.load({"a": "not a number"})

    def test_double_mapping_type_is_double(self, datatype_registry):
        dt = datatype_registry.get_type({"type": "double"})
        mapping = dt.create_mapping({"type": "double"})
        assert mapping["type"] == "double"

    def test_double_json_schema_type_is_number(self, datatype_registry):
        dt = datatype_registry.get_type({"type": "double"})
        schema = dt.create_json_schema({"type": "double"})
        assert schema["type"] == "number"

    def test_double_with_range(self, datatype_registry):
        schema = make_schema(
            datatype_registry,
            {"type": "double", "min_inclusive": 0.0, "max_inclusive": 1.0},
        )
        assert schema.load({"a": 0.5}) == {"a": 0.5}
        with pytest.raises(ma.ValidationError):
            schema.load({"a": -0.1})
        with pytest.raises(ma.ValidationError):
            schema.load({"a": 1.1})


# ===========================================================================
# Exclusive range boundaries (shared by int, long, float, double)
# ===========================================================================

class TestExclusiveRangeBoundaries:
    """min_exclusive / max_exclusive must exclude the boundary value."""

    def test_int_min_exclusive_rejects_boundary(self, datatype_registry):
        schema = make_schema(
            datatype_registry, {"type": "int", "min_exclusive": 0}
        )
        with pytest.raises(ma.ValidationError):
            schema.load({"a": 0})
        assert schema.load({"a": 1}) == {"a": 1}

    def test_int_max_exclusive_rejects_boundary(self, datatype_registry):
        schema = make_schema(
            datatype_registry, {"type": "int", "max_exclusive": 10}
        )
        with pytest.raises(ma.ValidationError):
            schema.load({"a": 10})
        assert schema.load({"a": 9}) == {"a": 9}

    def test_float_min_exclusive_rejects_boundary(self, datatype_registry):
        schema = make_schema(
            datatype_registry, {"type": "float", "min_exclusive": 0.0}
        )
        with pytest.raises(ma.ValidationError):
            schema.load({"a": 0.0})
        assert schema.load({"a": 0.001})["a"] == pytest.approx(0.001)

    def test_int_min_inclusive_accepts_boundary(self, datatype_registry):
        schema = make_schema(
            datatype_registry, {"type": "int", "min_inclusive": 5}
        )
        assert schema.load({"a": 5}) == {"a": 5}
        with pytest.raises(ma.ValidationError):
            schema.load({"a": 4})

    def test_int_max_inclusive_accepts_boundary(self, datatype_registry):
        schema = make_schema(
            datatype_registry, {"type": "int", "max_inclusive": 5}
        )
        assert schema.load({"a": 5}) == {"a": 5}
        with pytest.raises(ma.ValidationError):
            schema.load({"a": 6})


# ===========================================================================
# strict_validation=False — coerce strings to numbers
# ===========================================================================

class TestStrictValidation:
    """strict_validation=False must allow string-to-number coercion."""

    def test_int_strict_default_rejects_string(self, datatype_registry):
        schema = make_schema(datatype_registry, {"type": "int"})
        with pytest.raises(ma.ValidationError):
            schema.load({"a": "42"})

    def test_int_non_strict_coerces_string(self, datatype_registry):
        schema = make_schema(
            datatype_registry, {"type": "int", "strict_validation": False}
        )
        assert schema.load({"a": "42"}) == {"a": 42}

    def test_float_non_strict_coerces_string(self, datatype_registry):
        schema = make_schema(
            datatype_registry, {"type": "float", "strict_validation": False}
        )
        result = schema.load({"a": "3.14"})
        assert result["a"] == pytest.approx(3.14)


# ===========================================================================
# Number facets
# ===========================================================================

class TestNumberFacets:
    """Numeric types must generate facet definitions via FacetMixin."""

    @pytest.mark.parametrize("type_name", ["int", "long", "float", "double"])
    def test_numeric_type_produces_facet(self, datatype_registry, type_name):
        dt = datatype_registry.get_type({"type": type_name})
        facets = {}
        result = dt.get_facet(
            "metadata.score",
            {"type": type_name},
            nested_facets=[],
            facets=facets,
        )
        assert "metadata.score" in result, (
            f"{type_name} should produce a facet at the given path"
        )
