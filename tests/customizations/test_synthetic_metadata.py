#
# Copyright (c) 2026 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see https://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from oarepo_model.api import model
from oarepo_model.builder import InvenioModelBuilder
from oarepo_model.customizations.high_level.set_synthetic_metadata import (
    SetSyntheticMetadata,
)
from oarepo_model.presets.records_resources import records_preset
from oarepo_model.presets.records_resources.records.synthetic_metadata import (
    MetadataField,
    MetadataProxy,
)

# ---------------------------------------------------------------------------
# SetSyntheticMetadata customization
# ---------------------------------------------------------------------------


def test_set_synthetic_metadata_writes_keys_into_dictionary():
    m = MagicMock()
    type_registry = MagicMock()
    builder = InvenioModelBuilder(m, type_registry)
    builder.add_dictionary("synthetic_metadata")

    fn_a = lambda _: "value-a"  # noqa: E731
    fn_b = lambda d: d.get("title", "untitled")  # noqa: E731

    SetSyntheticMetadata(a=fn_a, b=fn_b).apply(builder, m)

    d = builder.get_dictionary("synthetic_metadata")
    assert d["a"] is fn_a
    assert d["b"] is fn_b


def test_set_synthetic_metadata_overrides_existing_keys():
    m = MagicMock()
    type_registry = MagicMock()
    builder = InvenioModelBuilder(m, type_registry)
    builder.add_dictionary("synthetic_metadata", default={"a": "old"})

    fn_a = lambda _: "new"  # noqa: E731
    SetSyntheticMetadata(a=fn_a).apply(builder, m)

    assert builder.get_dictionary("synthetic_metadata")["a"] is fn_a


# ---------------------------------------------------------------------------
# MetadataProxy
# ---------------------------------------------------------------------------


def test_metadata_proxy_returns_synthetic_when_key_missing():
    proxy = MetadataProxy({}, {"computed": lambda _: 42})
    assert proxy["computed"] == 42


def test_metadata_proxy_returns_real_value_when_present():
    proxy = MetadataProxy({"a": 1}, {"a": lambda _: 99})
    # Real keys take precedence over synthetic ones.
    assert proxy["a"] == 1


def test_metadata_proxy_synthetic_function_receives_wrapped_dict():
    wrapped = {"a": 1, "b": 2}
    proxy = MetadataProxy(wrapped, {"sum": lambda d: d["a"] + d["b"]})
    assert proxy["sum"] == 3


def test_metadata_proxy_unknown_key_raises_keyerror():
    proxy = MetadataProxy({}, {"computed": lambda _: 42})
    with pytest.raises(KeyError):
        _ = proxy["other"]


def test_synthetic_keys_accessible_only_through_getitem():
    proxy = MetadataProxy({"a": 1}, {"b": lambda _: 2})
    # ObjectProxy delegates iteration / membership to the wrapped object;
    # synthetic keys are accessed through __getitem__ but not advertised.
    assert dict(proxy) == {"a": 1}
    assert "a" in proxy
    assert "b" not in proxy
    assert proxy.get("a") == 1
    assert proxy.get("b") is None


# ---------------------------------------------------------------------------
# MetadataField
# ---------------------------------------------------------------------------

synthetic = {"title": lambda d: d["titles"][0]}


class Rec(dict):
    """Test pseudo-record class."""

    metadata = MetadataField(key="metadata", synthetic=synthetic)


def test_return_self():
    assert isinstance(Rec.metadata, MetadataField)


def test_metadata_field_wraps_dict_in_proxy_on_access():
    rec = Rec({"metadata": {"titles": ["title_1", "title_2"]}})
    md = rec.metadata
    assert isinstance(md, MetadataProxy)
    assert md["titles"] == ["title_1", "title_2"]
    assert md["title"] == "title_1"
    assert md == {"titles": ["title_1", "title_2"]}


# ---------------------------------------------------------------------------
# Preset wiring: building a model exposes synthetic_metadata + Record.metadata
# ---------------------------------------------------------------------------


_record_model_types = {
    "Metadata": {
        "properties": {
            "title": {"type": "fulltext+keyword"},
        }
    }
}


def test_records_preset_provides_synthetic_metadata_dictionary():
    m = model(
        name="synthetic_metadata_dict_test",
        version="1.0.0",
        presets=[records_preset],
        types=[_record_model_types],
        metadata_type="Metadata",
        customizations=[],
    )

    assert hasattr(m, "synthetic_metadata")
    assert m.synthetic_metadata == {}


def test_set_synthetic_metadata_in_built_model():
    m = model(
        name="synthetic_metadata_set_test",
        version="1.0.0",
        presets=[records_preset],
        types=[_record_model_types],
        metadata_type="Metadata",
        customizations=[
            SetSyntheticMetadata(
                title_upper=lambda d: d["title"].upper(),
            ),
        ],
    )

    assert "title_upper" in m.synthetic_metadata
    fn = m.synthetic_metadata["title_upper"]
    assert fn({"title": "abc"}) == "ABC"
