#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Module to generate record class."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from invenio_records.systemfields import ConstantField
from invenio_records_resources.records.api import Record as InvenioRecord
from invenio_records_resources.records.systemfields import IndexField

from oarepo_model.customizations import (
    AddClass,
    Customization,
    PrependMixin,
)
from oarepo_model.model import Dependency, InvenioModel
from oarepo_model.presets import Preset
from oarepo_model.presets.records_resources.records.synthetic_metadata import (
    MetadataField,
)

if TYPE_CHECKING:
    from collections.abc import Generator

    from oarepo_model.builder import InvenioModelBuilder


class RecordPreset(Preset):
    """Preset that generates a base record class."""

    depends_on = (
        "RecordMetadata",
        "PIDField",
        "PIDProvider",
        "PIDFieldContext",
        "synthetic_metadata",
    )

    provides = ("Record",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        class RecordMixin:
            """Base class for records in the model.

            This class extends InvenioRecord and can be customized further.
            """

            model_cls = Dependency("RecordMetadata")

            schema = ConstantField(
                "$schema",
                f"local://{model.base_name}-v{model.version}.json",
            )

            index = IndexField(
                f"{model.base_name}-metadata-v{model.version}",
            )

            pid = dependencies["PIDField"](
                provider=dependencies["PIDProvider"],
                context_cls=dependencies["PIDFieldContext"],
                create=True,
            )

            dumper = Dependency(
                "RecordDumper",
                "record_dumper_extensions",
                transform=lambda RecordDumper, record_dumper_extensions: RecordDumper(  # noqa: N803
                    record_dumper_extensions
                ),
            )

            if dependencies.get("synthetic_metadata"):
                metadata = MetadataField(key="metadata", synthetic=dependencies["synthetic_metadata"])
            else:
                metadata = InvenioRecord.metadata

        yield AddClass(
            "Record",
            clazz=InvenioRecord,
        )
        yield PrependMixin(
            "Record",
            RecordMixin,
        )
