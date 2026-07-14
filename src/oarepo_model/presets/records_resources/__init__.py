#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Records and resources presets for OARepo models.

This package provides presets for configuring Invenio records and resources
components including blueprints, services, API endpoints, and related functionality
for OARepo models.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .blueprints.blueprint_module import BlueprintModulePreset
from .blueprints.files.api_blueprint import ApiFilesBlueprintPreset
from .blueprints.records.api_blueprint import ApiBlueprintPreset
from .blueprints.records.app_blueprint import AppBlueprintPreset
from .ext import ExtPreset, FilesFeaturePreset, RecordsFeaturePreset
from .ext_files import ExtFilesPreset
from .files.file_metadata import FileMetadataPreset
from .files.file_record import FileRecordPreset
from .files.record import RecordWithFilesPreset
from .files.record_file_mapping import (
    RecordFileMappingPreset,
)
from .files.record_metadata import RecordMetadataWithFilesPreset
from .finalizers import FinalizationPreset
from .model_registration import ModelMetadataRegistrationPreset, ModelRegistrationPreset
from .proxy import ProxyPreset
from .records.dumper import RecordDumperPreset
from .records.jsonschema import JSONSchemaPreset
from .records.mapping import MappingPreset
from .records.metadata_json_schema import MetadataJSONSchemaPreset
from .records.metadata_mapping import MetadataMappingPreset
from .records.pid_provider import PIDProviderPreset
from .records.record import RecordPreset
from .records.record_json_schema import RecordJSONSchemaPreset
from .records.record_mapping import RecordMappingPreset
from .records.record_metadata import RecordMetadataPreset
from .records.record_with_relations import RecordWithRelationsPreset
from .records.relations import RelationsPreset
from .records.relations_dumper_ext import RelationsDumperExtPreset
from .records.synthetic_metadata import SyntheticMetadataPreset
from .resources.files.file_resource import FileResourcePreset
from .resources.files.file_resource_config import FileResourceConfigPreset
from .resources.records.exports import ExportsPreset
from .resources.records.imports import ImportsPreset
from .resources.records.json_deserializer import JSONDeserializerPreset
from .resources.records.register_ui_json_serializer import (
    RegisterJSONUISerializerPreset,
)
from .resources.records.resource import RecordResourcePreset
from .resources.records.resource_config import RecordResourceConfigPreset
from .resources.records.signposting import SignpostingPreset
from .resources.records.ui_json_serializer import JSONUISerializerPreset
from .services.files.file_record_service_components import (
    FileRecordServiceComponentsPreset,
)
from .services.files.file_service import FileServicePreset
from .services.files.file_service_config import FileServiceConfigPreset
from .services.files.record_with_files_schema import (
    RecordWithFilesSchemaPreset,
)
from .services.records.metadata_facets import MetadataFacetsPreset
from .services.records.metadata_schema import MetadataSchemaPreset
from .services.records.permission_policy import PermissionPolicyPreset
from .services.records.record_facets import RecordFacetsPreset
from .services.records.record_schema import RecordSchemaPreset
from .services.records.results import (
    RecordResultComponentsPreset,
    RecordResultItemPreset,
    RecordResultListPreset,
)
from .services.records.search_options import RecordSearchOptionsPreset
from .services.records.service import RecordServicePreset
from .services.records.service_config import RecordServiceConfigPreset
from .services.records.ui_metadata_schema import MetadataUISchemaPreset
from .services.records.ui_record_schema import RecordUISchemaPreset

if TYPE_CHECKING:
    from oarepo_model.presets import Preset

records_preset: list[type[Preset]] = [
    # record layer
    PIDProviderPreset,
    RecordPreset,
    RecordMetadataPreset,
    RecordDumperPreset,
    JSONSchemaPreset,
    MappingPreset,
    RecordJSONSchemaPreset,
    MetadataJSONSchemaPreset,
    RecordMappingPreset,
    MetadataMappingPreset,
    RelationsPreset,
    RecordWithRelationsPreset,
    RelationsDumperExtPreset,
    SyntheticMetadataPreset,
    # service layer
    RecordFacetsPreset,
    MetadataFacetsPreset,
    RecordServicePreset,
    RecordServiceConfigPreset,
    RecordResultComponentsPreset,
    RecordResultItemPreset,
    RecordResultListPreset,
    RecordSearchOptionsPreset,
    PermissionPolicyPreset,
    RecordSchemaPreset,
    MetadataSchemaPreset,
    RecordUISchemaPreset,
    MetadataUISchemaPreset,
    # resource layer
    ExportsPreset,
    SignpostingPreset,
    ImportsPreset,
    JSONDeserializerPreset,
    RecordResourcePreset,
    RecordResourceConfigPreset,
    JSONUISerializerPreset,
    RegisterJSONUISerializerPreset,
    # extension
    ExtPreset,
    ProxyPreset,
    BlueprintModulePreset,
    ApiBlueprintPreset,
    AppBlueprintPreset,
    ModelRegistrationPreset,
    ModelMetadataRegistrationPreset,
    FinalizationPreset,
    # feature
    RecordsFeaturePreset,
]

files_preset: list[type[Preset]] = [
    # file layer
    FileRecordPreset,
    RecordWithFilesPreset,
    RecordMetadataWithFilesPreset,
    FileMetadataPreset,
    # record layer
    RecordFileMappingPreset,
    # service layer
    FileRecordServiceComponentsPreset,
    FileServiceConfigPreset,
    FileServicePreset,
    RecordWithFilesSchemaPreset,
    # resource layer
    FileResourcePreset,
    FileResourceConfigPreset,
    # extension
    ExtFilesPreset,
    ApiFilesBlueprintPreset,
    # feature
    FilesFeaturePreset,
]

records_resources_preset: list[type[Preset]] = records_preset + files_preset
