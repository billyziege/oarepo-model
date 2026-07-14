#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""High-level customizations for OARepo model builder.

This package contains high-level customizations that provide convenient
abstractions for common model modifications. These customizations combine
multiple low-level operations to achieve complex model transformations
with simple, declarative interfaces.
"""

from __future__ import annotations

from .add_export import AddMetadataExport
from .add_import import AddMetadataImport
from .add_link import AddLink
from .add_pid_relation import AddPIDRelation
from .add_search_fields import SetDefaultSearchFields
from .add_service_component import AddServiceComponent
from .index_mapping import PatchIndexMapping, PatchIndexPropertyMapping
from .index_settings import (
    PatchIndexSettings,
    SetIndexNestedFieldsLimit,
    SetIndexTotalFieldsLimit,
)
from .set_permission_policy import SetPermissionPolicy
from .set_synthetic_metadata import SetSyntheticMetadata

__all__ = (
    "AddLink",
    "AddMetadataExport",
    "AddMetadataImport",
    "AddPIDRelation",
    "AddServiceComponent",
    "PatchIndexMapping",
    "PatchIndexPropertyMapping",
    "PatchIndexSettings",
    "SetDefaultSearchFields",
    "SetIndexNestedFieldsLimit",
    "SetIndexTotalFieldsLimit",
    "SetPermissionPolicy",
    "SetSyntheticMetadata",
)
