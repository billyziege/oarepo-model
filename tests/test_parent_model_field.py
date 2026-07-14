#
# Copyright (c) 2026 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see https://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
from __future__ import annotations


def test_parent_model_field(
    identity_simple,
    model_types,
    draft_model,
    draft_model_with_files,
    location,
    search_clear,
):
    draft_model.proxies.current_service.create(identity_simple, data={})
    draft_model_with_files.proxies.current_service.create(identity_simple, data={"files": {"enabled": True}})

    assert draft_model.ParentRecordMetadata.query.one().model == "draft_test"
    assert draft_model_with_files.ParentRecordMetadata.query.one().model == "draft_with_files"
