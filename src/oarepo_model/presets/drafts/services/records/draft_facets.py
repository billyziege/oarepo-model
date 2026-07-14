#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Module to generate draft-specific facets."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from oarepo_runtime.services.facets.utils import build_facet

from oarepo_model.customizations import (
    AddToDictionary,
    AddToModule,
    Customization,
)
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class DraftFacetsPreset(Preset):
    """Preset for draft-specific facets (is_published)."""

    provides = ("DraftFacets",)
    modifies = ("RecordFacets",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        draft_facets: dict[str, list[dict[str, str | object]]] = {
            "is_published": [
                {
                    "facet": "invenio_records_resources.services.records.facets.TermsFacet",
                    "field": "is_published",
                }
            ],
        }

        search_options_facets = {}
        for facet_name, facet_def in draft_facets.items():
            yield AddToModule("facets", facet_name, build_facet(facet_def))
            search_options_facets[facet_name] = build_facet(facet_def)

        yield AddToDictionary("RecordFacets", search_options_facets)
