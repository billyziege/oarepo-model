#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Module to generate record schema class."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast, override

from oarepo_model.customizations import (
    AddDictionary,
    AddModule,
    AddToDictionary,
    AddToModule,
    Customization,
)
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel

from oarepo_runtime.services.facets.utils import build_facet


class RecordFacetsPreset(Preset):
    """Preset for record service class."""

    provides = ("RecordFacets",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        yield AddModule("facets")
        yield AddDictionary("RecordFacets", {})

        if model.record_type is not None:
            facets = get_facets(builder, model.record_type)
            search_options_facets = {}

            for f in facets:
                yield AddToModule("facets", f, build_facet(facets[f]))
                search_options_facets[f] = build_facet(facets[f])
            yield AddToDictionary("RecordFacets", search_options_facets)


def get_facets(
    builder: InvenioModelBuilder,
    schema_type: Any,
    prefix: str = "",
) -> Any:
    """Get the marshmallow schema for a given schema type."""
    if isinstance(schema_type, (str, dict)):
        datatype = builder.type_registry.get_type(schema_type)
        return cast("Any", datatype).get_facet(prefix, {} if isinstance(schema_type, str) else schema_type, [], {})
    return {}
