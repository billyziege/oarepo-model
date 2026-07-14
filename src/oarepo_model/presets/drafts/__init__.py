#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Draft-related presets for Invenio draft/publish workflows.

This module provides presets for implementing draft record functionality,
including file handling, record management, and API blueprints for
draft-enabled Invenio repositories.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .blueprints.files.api_draft_files_blueprint import ApiDraftFilesBlueprintPreset
from .blueprints.files.api_draft_media_files_blueprint import (
    ApiDraftMediaFilesBlueprintPreset,
)
from .blueprints.files.api_media_files_blueprint import ApiMediaFilesBlueprintPreset
from .ext import DraftsFilesFeaturePreset, DraftsRecordsFeaturePreset
from .ext_draft_files import ExtDraftFilesPreset
from .ext_draft_media_files import ExtDraftMediaFilesPreset
from .ext_media_files import ExtMediaFilesPreset
from .files.draft_media_files import DraftMediaFilesPreset
from .files.draft_with_files import DraftWithFilesPreset
from .files.draft_with_files_metadata import DraftMetadataWithFilesPreset
from .files.draft_with_media_files import DraftWithMediaFilesPreset
from .files.file_draft import FileDraftPreset
from .files.file_draft_metadata import FileDraftMetadataPreset
from .files.media_file_draft import MediaFileDraftPreset
from .files.media_file_draft_metadata import MediaFileDraftMetadataPreset
from .files.media_file_metadata import MediaFileMetadataPreset
from .files.media_file_record import MediaFileRecordPreset
from .files.record_file_mapping import RecordFileMappingPreset
from .files.record_media_files import RecordMediaFilesPreset
from .files.record_with_files import RecordWithFilesPreset
from .files.record_with_files_metadata import RecordMetadataWithFilesPreset
from .files.record_with_media_files import RecordWithMediaFilesPreset
from .records.draft_mapping import DraftMappingPreset
from .records.draft_record import DraftPreset
from .records.draft_record_metadata import DraftMetadataPreset
from .records.draft_with_relations import DraftWithRelationsPreset
from .records.parent_pid_provider import ParentPIDProviderPreset
from .records.parent_record import ParentRecordPreset
from .records.parent_record_metadata import ParentRecordMetadataPreset
from .records.parent_record_state import ParentRecordStatePreset
from .records.pid_provider import PIDProviderPreset
from .records.published_record_metadata_with_parent import (
    RecordMetadataWithParentPreset,
)
from .records.published_record_with_parent import RecordWithParentPreset
from .resources.files.draft_file_resource import DraftFileResourcePreset
from .resources.files.draft_file_resource_config import DraftFileResourceConfigPreset
from .resources.files.draft_media_file_resource import DraftMediaFileResourcePreset
from .resources.files.draft_media_file_resource_config import (
    DraftMediaFileResourceConfigPreset,
)
from .resources.files.media_file_resource import MediaFileResourcePreset
from .resources.files.media_file_resource_config import MediaFileResourceConfigPreset
from .resources.records.resource import DraftResourcePreset
from .resources.records.resource_config import DraftResourceConfigPreset
from .resources.records.ui_record_schema import DraftsRecordUISchemaPreset
from .services.files.draft_file_record_service_components import (
    DraftFileRecordServiceComponentsPreset,
)
from .services.files.draft_file_service import DraftFileServicePreset
from .services.files.draft_file_service_config import DraftFileServiceConfigPreset
from .services.files.draft_media_file_service import DraftMediaFileServicePreset
from .services.files.draft_media_file_service_config import (
    DraftMediaFileServiceConfigPreset,
)
from .services.files.media_file_service import MediaFileServicePreset
from .services.files.media_file_service_config import MediaFileServiceConfigPreset
from .services.files.media_files_record_service_components import (
    FileRecordServiceComponentsPreset,
)
from .services.files.media_files_record_service_config import (
    MediaFilesRecordServiceConfigPreset,
)
from .services.files.no_upload_file_service_config import (
    NoUploadFileServiceConfigPreset,
)
from .services.records.draft_facets import DraftFacetsPreset
from .services.records.parent_record_schema import ParentRecordSchemaPreset
from .services.records.record_schema import DraftRecordSchemaPreset
from .services.records.relations import RelationsServiceComponentPreset
from .services.records.search_options import DraftSearchOptionsPreset
from .services.records.service import DraftServicePreset
from .services.records.service_config import DraftServiceConfigPreset

if TYPE_CHECKING:
    from oarepo_model.presets import Preset


drafts_records_preset: list[type[Preset]] = [
    # records layer
    ParentRecordMetadataPreset,
    DraftMetadataPreset,
    RecordMetadataWithParentPreset,
    ParentRecordStatePreset,
    ParentRecordPreset,
    RecordWithParentPreset,
    DraftPreset,
    PIDProviderPreset,
    ParentPIDProviderPreset,
    DraftMappingPreset,
    DraftWithRelationsPreset,
    # service layer
    DraftServiceConfigPreset,
    DraftServicePreset,
    DraftRecordSchemaPreset,
    RelationsServiceComponentPreset,
    ParentRecordSchemaPreset,
    DraftSearchOptionsPreset,
    DraftFacetsPreset,
    # resource layer
    DraftResourcePreset,
    DraftResourceConfigPreset,
    DraftsRecordUISchemaPreset,
    # feature
    DraftsRecordsFeaturePreset,
]

drafts_files_preset: list[type[Preset]] = [
    # records layer
    MediaFileRecordPreset,
    MediaFileDraftPreset,
    FileDraftPreset,
    RecordWithMediaFilesPreset,
    RecordMediaFilesPreset,
    RecordWithFilesPreset,
    RecordMetadataWithFilesPreset,
    DraftWithFilesPreset,
    DraftWithMediaFilesPreset,
    DraftMediaFilesPreset,
    DraftMetadataWithFilesPreset,
    MediaFileMetadataPreset,
    MediaFileDraftMetadataPreset,
    FileDraftMetadataPreset,
    # record layer
    RecordFileMappingPreset,
    # service layer
    MediaFilesRecordServiceConfigPreset,
    DraftFileRecordServiceComponentsPreset,
    FileRecordServiceComponentsPreset,
    DraftFileServiceConfigPreset,
    NoUploadFileServiceConfigPreset,
    MediaFileServiceConfigPreset,
    DraftMediaFileServiceConfigPreset,
    DraftFileServicePreset,
    DraftMediaFileServicePreset,
    MediaFileServicePreset,
    # resource layer
    DraftFileResourceConfigPreset,
    DraftFileResourcePreset,
    MediaFileResourceConfigPreset,
    MediaFileResourcePreset,
    DraftMediaFileResourceConfigPreset,
    DraftMediaFileResourcePreset,
    # ext
    ExtDraftFilesPreset,
    ExtMediaFilesPreset,
    ExtDraftMediaFilesPreset,
    # blueprints
    ApiDraftFilesBlueprintPreset,
    ApiMediaFilesBlueprintPreset,
    ApiDraftMediaFilesBlueprintPreset,
    # feature
    DraftsFilesFeaturePreset,
]

drafts_preset = drafts_records_preset + drafts_files_preset
