#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see https://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from oarepo_model.builder import InvenioModelBuilder
from oarepo_model.customizations import (
    AddToDictionary,
)


def test_add_to_dictionary():
    model = MagicMock()
    type_registry = MagicMock()
    builder = InvenioModelBuilder(model, type_registry)
    builder.add_dictionary("ADict")

    AddToDictionary("ADict", key="a", value="b").apply(builder, model)
    assert builder.get_dictionary("ADict")["a"] == "b"

    with pytest.raises(ValueError, match="Key 'a' already exists in dictionary 'ADict'"):
        AddToDictionary("ADict", key="a", value="b").apply(builder, model)

    AddToDictionary("ADict", key="a", value="c", exists_ok=True).apply(builder, model)
    assert builder.get_dictionary("ADict")["a"] == "c"

    AddToDictionary("ADict", key="a", value="d", patch=True).apply(builder, model)
    assert builder.get_dictionary("ADict")["a"] == "d"

    AddToDictionary("BDict", {"a": "1"}).apply(builder, model)
    assert builder.get_dictionary("BDict")["a"] == "1"


def test_add_to_dictionary_override_values():
    model = MagicMock()
    type_registry = MagicMock()
    builder = InvenioModelBuilder(model, type_registry)
    builder.add_dictionary("CDict")

    AddToDictionary("CDict", {"a": "1", "nested": {"x": "original"}}).apply(builder, model)

    AddToDictionary(
        "CDict",
        {"a": "2", "b": "3", "nested": {"x": "new", "y": "added"}},
        override_values=True,
    ).apply(builder, model)
    assert builder.get_dictionary("CDict") == {
        "a": "2",
        "b": "3",
        "nested": {"x": "new", "y": "added"},
    }

    builder.add_dictionary("DDict")
    AddToDictionary("DDict", {"a": "1", "nested": {"x": "original"}}).apply(builder, model)

    AddToDictionary(
        "DDict",
        {"a": "2", "b": "3", "nested": {"x": "new", "y": "added"}},
        override_values=False,
    ).apply(builder, model)
    assert builder.get_dictionary("DDict") == {
        "a": "1",
        "b": "3",
        "nested": {"x": "original"},
    }
