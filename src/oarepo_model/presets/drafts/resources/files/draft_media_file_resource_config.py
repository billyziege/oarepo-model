#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Preset for configuring draft media file resource.

This module provides a preset that creates and configures a DraftMediaFileResourceConfig
for draft media file REST API endpoints. It sets up the blueprint name and URL prefix
for accessing media files on draft records.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from invenio_records_resources.resources import FileResourceConfig

from oarepo_model.customizations import (
    AddClass,
    Customization,
    PrependMixin,
)
from oarepo_model.model import Dependency, InvenioModel
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder


class DraftMediaFileResourceConfigPreset(Preset):
    """Preset for file resource config class."""

    provides = ("DraftMediaFileResourceConfig",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        class DraftMediaFileResourceConfigMixin:
            blueprint_name = f"{model.base_name}_draft_media_files"
            url_prefix = f"/{model.slug}/<pid_value>/draft"
            # Response handling
            response_handlers = Dependency("media_file_response_handlers")

        yield AddClass("DraftMediaFileResourceConfig", clazz=FileResourceConfig)
        yield PrependMixin(
            "DraftMediaFileResourceConfig",
            DraftMediaFileResourceConfigMixin,
        )
