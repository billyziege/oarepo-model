#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see https://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
from __future__ import annotations


def test_facet(
    app,
    facet_service,
    identity_simple,
    input_facets_data,
    facet_model,
    search,
    search_clear,
    location,
):
    Record = facet_model.Record
    Draft = facet_model.Draft
    item = facet_service.create(identity_simple, input_facets_data)
    id_ = item.id
    facet_service.publish(identity_simple, id_)

    assert not hasattr(facet_model.facets, "metadata.c")
    assert not hasattr(facet_model.facets, "metadata.jazyk")
    assert not hasattr(facet_model.facets, "metadata.multi")

    assert hasattr(facet_model.facets, "metadata.languages")
    assert not hasattr(facet_model.facets, "metadata.languages[]")

    assert hasattr(facet_model.facets, "metadata.vlastni")
    assert hasattr(facet_model.facets, "metadata.b")
    assert hasattr(facet_model.facets, "metadata.obyc_array")

    Record.index.refresh()
    Draft.index.refresh()
    hit = facet_service.search(identity_simple, q=f"id:{id_}", size=25, page=1, facets={"metadata.b": ["jej"]})

    no_hit = facet_service.search(identity_simple, q=f"id:{id_}", size=25, page=1, facets={"metadata.b": ["xy"]})
    assert hit.total == 1
    assert no_hit.total == 0


def test_draft_facets_preset_adds_is_published_facet(
    app,
    facet_service,
    identity_simple,
    input_facets_data,
    facet_model,
    search,
    search_clear,
    location,
):
    """Test that DraftFacetsPreset adds is_published facet to search options."""
    assert hasattr(facet_model.facets, "is_published")
