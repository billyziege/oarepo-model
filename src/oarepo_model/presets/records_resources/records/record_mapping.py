#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Module to generate record mapping json file."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast, override

from deepmerge import always_merger

from oarepo_model.customizations import AddJSONFile, Customization
from oarepo_model.datatypes.collections import ObjectDataType
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class RecordMappingPreset(Preset):
    """Preset for record service class."""

    modifies = ("mappings",)
    provides = ("record-mapping",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        mapping = {"mappings": get_mapping(builder, model.record_type)} if model.record_type is not None else {}

        mapping = always_merger.merge(
            {
                "mappings": {
                    "dynamic": True,
                    "properties": {
                        "$schema": {"type": "keyword"},
                        "id": {"type": "keyword"},
                        "created": {"type": "date"},
                        "updated": {"type": "date"},
                        "expires_at": {"type": "date"},
                        "indexed_at": {"type": "date"},
                        "uuid": {"type": "keyword"},
                        "version_id": {"type": "integer"},
                        "pid": {
                            "properties": {
                                "obj_type": {"type": "keyword", "index": False},
                                "pid_type": {"type": "keyword", "index": False},
                                "pk": {"type": "long", "index": False},
                                "status": {"type": "keyword", "index": False},
                            },
                        },
                    },
                },
            },
            mapping,
        )

        yield AddJSONFile(
            "record-mapping",
            "mappings",
            f"os-v2/{model.base_name}/metadata-v{model.version}.json",
            mapping,
        )


def get_mapping(builder: InvenioModelBuilder, schema_type: Any) -> dict[str, Any]:
    """Get the mapping for the given schema type."""
    base_mapping: dict[str, Any]
    if isinstance(schema_type, (str, dict)):
        datatype = builder.type_registry.get_type(schema_type)
        base_mapping = cast("Any", datatype).create_mapping(
            {} if isinstance(schema_type, str) else schema_type,
        )
    elif isinstance(schema_type, ObjectDataType):
        base_mapping = schema_type.create_mapping({})
    else:
        raise TypeError(
            f"Invalid schema type: {schema_type}. Expected str, dict or None.",
        )
    base_mapping_copy = {**base_mapping}
    base_mapping_copy.pop("type", None)
    return base_mapping_copy
