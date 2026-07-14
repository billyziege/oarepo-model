#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Preset for creating parent record metadata model.

This module provides a preset that creates a ParentRecordMetadata database
model for storing parent record information. The parent record serves as
a stable container for managing versions and drafts of conceptual records.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from invenio_db import db
from invenio_records.models import RecordMetadataBase
from sqlalchemy import String

from oarepo_model.customizations import (
    AddBaseClass,
    AddClass,
    AddClassField,
    Customization,
)
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class ParentRecordMetadataPreset(Preset):
    """Preset for parent record metadata class."""

    provides = ("ParentRecordMetadata",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        yield AddClass("ParentRecordMetadata")
        yield AddClassField(
            "ParentRecordMetadata",
            "__tablename__",
            f"{builder.model.base_name}_parent_metadata",
        )
        yield AddClassField(
            "ParentRecordMetadata",
            "model",
            db.Column(String, default=builder.model.base_name),
        )
        yield AddBaseClass("ParentRecordMetadata", db.Model)
        yield AddBaseClass("ParentRecordMetadata", RecordMetadataBase)
