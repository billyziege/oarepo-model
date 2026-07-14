#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Data type wrapper implementation for oarepo-model.

This module provides the WrappedDataType class that wraps dictionary-based
type definitions and delegates to the actual implementation through the
data type registry.
"""

from __future__ import annotations

import copy
from functools import cached_property
from typing import TYPE_CHECKING, Any, cast, override

import deepmerge

from .base import DataType

if TYPE_CHECKING:
    from collections.abc import Mapping

    import marshmallow

    from oarepo_model.customizations.base import Customization

    from .collections import ObjectDataType
    from .registry import DataTypeRegistry


class WrappedDataType(DataType):
    """A datatype that wraps a dictionary defining the type."""

    def __init__(
        self,
        registry: DataTypeRegistry,
        name: str,
        type_dict: dict[str, Any],
    ):
        """Initialize the WrappedDataType with a registry, name, and type dictionary."""
        super().__init__(registry, name)
        self.type_dict = type_dict
        self._impl: DataType | None = None

    @cached_property
    def impl(self) -> DataType:
        """Get the implementation of the wrapped data type."""
        return self._registry.get_type(self.type_dict)

    def _merge_type_dict(self, element: dict[str, Any]) -> dict[str, Any]:
        """Merge the type_dict with the element dictionary.

        This is used to create a new type dictionary that includes the properties of the element.
        """
        element_without_type = {
            key: value
            for key, value in element.items()
            if key != "type"  # remove type to avoid conflicts
        }
        return cast(
            "dict[str, Any]",
            deepmerge.always_merger.merge(copy.deepcopy(self.type_dict), element_without_type),
        )

    @override
    def create_marshmallow_field(
        self,
        field_name: str,
        element: dict[str, Any],
    ) -> marshmallow.fields.Field:
        """Create a Marshmallow field for the data type.

        This method should be overridden by subclasses to provide specific field creation logic.
        """
        # to create a marshmallow field, we need to merge the element with the type_dict
        return self.impl.create_marshmallow_field(
            field_name,
            self._merge_type_dict(element),
        )

    @override
    def create_ui_marshmallow_fields(
        self,
        field_name: str,
        element: dict[str, Any],
    ) -> dict[str, marshmallow.fields.Field]:
        """Create a Marshmallow UI field for the wrapped data type.

        This method should be overridden by subclasses to provide specific field creation logic.
        """
        # to create a marshmallow field, we need to merge the element with the type_dict
        return self.impl.create_ui_marshmallow_fields(
            field_name,
            self._merge_type_dict(element),
        )

    def create_marshmallow_schema(
        self,
        element: dict[str, Any],
    ) -> type[marshmallow.Schema]:
        """Create a Marshmallow schema for the wrapped data type.

        This method should be overridden by subclasses to provide specific schema creation logic.
        """
        return cast("ObjectDataType", self.impl).create_marshmallow_schema(
            self._merge_type_dict(element),
        )

    def get_facet(
        self,
        path: str,
        element: dict[str, Any],
        nested_facets: list[Any],
        facets: dict[str, list],
        path_suffix: str = "",
    ) -> Any:
        """Create facets for the wrapped data type."""
        return cast("ObjectDataType", self.impl).get_facet(
            path,
            element=self._merge_type_dict(element),
            nested_facets=nested_facets,
            facets=facets,
            path_suffix=path_suffix,
        )

    def create_ui_marshmallow_schema(
        self,
        element: dict[str, Any],
    ) -> type[marshmallow.Schema]:
        """Create a Marshmallow schema for the wrapped data type.

        This method should be overridden by subclasses to provide specific schema creation logic.
        """
        return cast("ObjectDataType", self.impl).create_ui_marshmallow_schema(
            self._merge_type_dict(element),
        )

    @override
    def create_json_schema(self, element: dict[str, Any]) -> Mapping[str, Any]:
        return self.impl.create_json_schema(self._merge_type_dict(element))

    @override
    def create_mapping(self, element: dict[str, Any]) -> Mapping[str, Any]:
        return self.impl.create_mapping(self._merge_type_dict(element))

    @override
    def create_relations(
        self,
        element: dict[str, Any],
        path: list[tuple[str, dict[str, Any]]],
    ) -> list[Customization]:
        return self.impl.create_relations(self._merge_type_dict(element), path)

    @override
    def create_ui_model(
        self,
        element: dict[str, Any],
        path: list[str],
    ) -> dict[str, Any]:
        return self.impl.create_ui_model(self._merge_type_dict(element), path)
