#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Preset for draft record API model.

This module provides the DraftRecordPreset that creates
draft record API classes for the draft/publish workflow.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from invenio_drafts_resources.records import Draft as InvenioDraft
from invenio_pidstore.models import PIDStatus
from invenio_rdm_records.records.systemfields import HasDraftCheckField
from invenio_records.systemfields import ConstantField
from invenio_records_resources.records.systemfields import (
    IndexField,
    PIDStatusCheckField,
)
from oarepo_runtime.records.systemfields import PublicationStatusSystemField

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


class DraftPreset(Preset):
    """Preset for Draft record."""

    depends_on = (
        "RecordMetadata",
        "PIDField",
        "PIDProvider",
        "PIDFieldContext",
        "synthetic_metadata",
    )

    provides = ("Draft",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:
        class DraftMixin:
            """Base class for records in the model.

            This class extends InvenioRecord and can be customized further.
            """

            model_cls = Dependency("DraftMetadata")
            versions_model_cls = Dependency("ParentRecordState")
            parent_record_cls = Dependency("ParentRecord")

            schema = ConstantField(
                "$schema",
                f"local://{builder.model.base_name}-v{model.version}.json",
            )

            index = IndexField(
                f"{builder.model.base_name}-draft-metadata-v{model.version}",
                search_alias=f"{builder.model.base_name}",
            )

            pid = dependencies["PIDField"](
                provider=dependencies["PIDProvider"],
                context_cls=dependencies["PIDFieldContext"],
                create=True,
                delete=False,
            )

            dumper = Dependency(
                "RecordDumper",
                "record_dumper_extensions",
                transform=lambda RecordDumper, record_dumper_extensions: RecordDumper(  # noqa: N803
                    record_dumper_extensions
                ),
            )

            # note: we need to use the has_draft field from rdm records
            # even if this is the draft record - unfortunately the system field
            # is defined in the invenio-rdm-records package
            has_draft = HasDraftCheckField()

            publication_status = PublicationStatusSystemField()

            # This system field originates in invenio-rdm-records and is used on
            # both published records and drafts. On the draft side, it allows
            # the draft record to expose whether its PID is in a "published"
            # (REGISTERED) state, so that search/indexing and services can
            # consistently filter by publication status across both record types.
            is_published = PIDStatusCheckField(status=PIDStatus.REGISTERED, dump=True)

            if dependencies.get("synthetic_metadata"):
                metadata = MetadataField(key="metadata", synthetic=dependencies["synthetic_metadata"])
            else:
                metadata = InvenioDraft.metadata

        yield AddClass(
            "Draft",
            clazz=InvenioDraft,
        )
        yield PrependMixin(
            "Draft",
            DraftMixin,
        )
