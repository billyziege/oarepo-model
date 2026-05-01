#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see https://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Tests: root-level mapping must use dynamic:true, not dynamic:strict.

InvenioRDM's record indexer adds system fields (is_published, parent,
versions, has_draft, deletion_status, ...) that are not part of the
oarepo model schema. With dynamic:strict these cause a
strict_dynamic_mapping_exception. The root must be dynamic:true so
OpenSearch auto-maps them; the metadata subtree keeps dynamic:strict
through ObjectDataType.
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest

from oarepo_model.builder import InvenioModelBuilder
from oarepo_model.customizations import AddModule
from oarepo_model.presets.records_resources.records.record_mapping import (
    RecordMappingPreset,
)


@pytest.fixture
def minimal_model():
    """Minimal InvenioModel-like mock with no record schema."""
    m = MagicMock()
    m.record_type = None
    m.base_name = "testrecord"
    m.version = "1.0.0"
    return m


def _build_mapping(model):
    """Run RecordMappingPreset and return the parsed mapping dict."""
    type_registry = MagicMock()
    builder = InvenioModelBuilder(model, type_registry)
    AddModule("testrecord").apply(builder, model)
    preset = RecordMappingPreset()
    for customization in preset.apply(builder, model, {}):
        customization.apply(builder, model)
    return json.loads(builder.get_file("record-mapping").content)


class TestRecordMappingDynamic:
    """Root mapping must allow InvenioRDM system fields via dynamic:true."""

    def test_root_dynamic_is_true_not_strict(self, minimal_model):
        """Root-level 'dynamic' must be True, not 'strict'.

        dynamic:strict at the root causes strict_dynamic_mapping_exception
        for every InvenioRDM record because the indexer adds system fields
        (is_published, parent, versions, has_draft, etc.) that are absent
        from the oarepo schema definition.
        """
        mapping = _build_mapping(minimal_model)
        root_dynamic = mapping["mappings"]["dynamic"]
        assert root_dynamic is not False, "dynamic:false would block all unknown fields"
        assert root_dynamic != "strict", (
            "dynamic:strict at the root causes strict_dynamic_mapping_exception for "
            "InvenioRDM system fields (is_published, parent, versions, etc.) that the "
            "indexer adds but the oarepo schema does not define."
        )
        assert root_dynamic is True or root_dynamic == "true", (
            f"Expected dynamic:true at the root, got {root_dynamic!r}"
        )

    def test_standard_invenio_fields_are_present(self, minimal_model):
        """Core InvenioRDM base fields must always be in the mapping."""
        mapping = _build_mapping(minimal_model)
        props = mapping["mappings"]["properties"]
        for field in ("id", "created", "updated", "uuid", "version_id"):
            assert field in props, f"Expected base field '{field}' in mapping properties"
