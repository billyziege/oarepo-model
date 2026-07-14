#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Base classes and interfaces for OARepo data types.

This module provides the foundational DataType class and related interfaces
that define how data types are implemented and used within OARepo models.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, cast

from invenio_base.utils import obj_or_import_string
from marshmallow.fields import Field
from oarepo_runtime.services.facets.utils import get_basic_facet

if TYPE_CHECKING:
    from oarepo_model.customizations.base import Customization

    from .registry import DataTypeRegistry

ARRAY_ITEM_PATH = "[]"


class DataType:
    """Base class for data types in the Oarepo model.

    This class can be extended to create custom data types.
    """

    TYPE = "base"

    marshmallow_field_class: type[Field] | None = None
    jsonschema_type: str | Mapping[str, Any] | None = None
    mapping_type: str | Mapping[str, Any] | None = None

    def __init__(self, registry: DataTypeRegistry, name: str | None = None):
        """Initialize the data type with a registry.

        :param registry: The registry to which this data type belongs.
        """
        self._registry = registry
        self._name = name or self.TYPE

    @property
    def facet_name(self) -> str:
        """Define facet class."""
        return "invenio_records_resources.services.records.facets.TermsFacet"

    @property
    def name(self) -> str:
        """Get the name of the data type.

        :return: The name of the data type.
        """
        return self._name

    def create_marshmallow_field(
        self,
        field_name: str,
        element: dict[str, Any],
    ) -> Field:
        """Create a Marshmallow field for the data type.

        This method should be overridden by subclasses to provide specific field creation logic.
        """
        if element.get("marshmallow_field") is not None:
            # if marshmallow_field is specified, use it directly
            marshmallow_field = obj_or_import_string(element["marshmallow_field"])
            if marshmallow_field is None or not isinstance(marshmallow_field, Field):
                raise TypeError(
                    f"marshmallow_field must be an instance of marshmallow.fields.Field, got {marshmallow_field}",
                )
            return marshmallow_field

        return self._get_marshmallow_field_class(field_name, element)(
            **self._get_marshmallow_field_args(field_name, element),
        )

    def _get_ui_marshmallow_field_class(
        self,
        field_name: str,  # noqa: ARG002 for override
        element: dict[str, Any],
    ) -> type | None:
        """Get a ui marshmallow field class."""
        if element.get("ui_marshmallow_field_class"):
            return cast("type", obj_or_import_string(element["ui_marshmallow_field_class"]))
        return None

    def get_facet(
        self,
        path: str,
        element: dict[str, Any],
        nested_facets: list[Any],
        facets: dict[str, list],
        path_suffix: str = "",
    ) -> Any:
        """Create facets for the data type."""
        _, _, _, _, _ = path, element, nested_facets, facets, path_suffix

        return facets

    def create_ui_marshmallow_fields(
        self,
        field_name: str,  # noqa: ARG002 for override
        element: dict[str, Any],  # noqa: ARG002 for override
    ) -> dict[str, Field]:
        """Create a Marshmallow UI field for the data type.

        This method should be overridden by subclasses to provide specific UI field creation logic.
        """
        # if there is no UI transformation, leave it out, therefore there are no copied values in UI
        return {}

    def _get_marshmallow_field_class(
        self,
        field_name: str,  # noqa: ARG002 for override
        element: dict[str, Any],
    ) -> type[Field]:
        """Get the Marshmallow field class for the data type.

        This method can be overridden by subclasses to provide specific field class logic.
        """
        if element.get("marshmallow_field_class") is not None:
            imported = obj_or_import_string(element["marshmallow_field_class"])
            if not isinstance(imported, type) or not issubclass(imported, Field):
                raise TypeError(
                    f"marshmallow_field_class must be a subclass of marshmallow.fields.Field, got {imported}",
                )
            return imported

        if self.marshmallow_field_class is None:
            raise NotImplementedError(
                "Subclasses must either provide marshmallow_field_class or "
                "implement this method to provide field class logic.",
            )
        return self.marshmallow_field_class

    def _get_marshmallow_field_args(
        self,
        field_name: str,
        element: dict[str, Any],
    ) -> dict[str, Any]:
        """Get the arguments for the Marshmallow field.

        This method can be overridden by subclasses to provide specific field arguments logic.
        """
        return {
            "required": element.get("required", False),
            "allow_none": element.get("allow_none", False),
            "dump_only": element.get("dump_only", False),
            "load_only": element.get("load_only", False),
            "attribute": field_name,
            "data_key": field_name,
        }

    def create_json_schema(
        self,
        element: dict[str, Any],  # noqa: ARG002 for override
    ) -> Mapping[str, Any]:
        """Create a JSON schema for the data type.

        This method should be overridden by subclasses to provide specific JSON schema creation logic.
        """
        if self.jsonschema_type is not None:
            if isinstance(self.jsonschema_type, Mapping):
                return self.jsonschema_type

            return {"type": self.jsonschema_type}

        raise NotImplementedError(
            f"{self.__class__.__name__} neither implements create_json_schema nor provides self.jsonschema_type",
        )

    def create_mapping(
        self,
        element: dict[str, Any],  # noqa: ARG002 for override
    ) -> Mapping[str, Any]:
        """Create a mapping for the data type.

        This method can be overridden by subclasses to provide specific mapping creation logic.
        """
        if self.mapping_type is not None:
            if isinstance(self.mapping_type, Mapping):
                return self.mapping_type
            return {"type": self.mapping_type}

        raise NotImplementedError(
            f"{self.__class__.__name__} neither implements create_mapping nor provides self.mapping_type",
        )

    def create_relations(
        self,
        element: dict[str, Any],  # noqa: ARG002 for override
        path: list[tuple[str, dict[str, Any]]],  # noqa: ARG002 for override
    ) -> list[Customization]:
        """Create relations for the data type.

        This method can be overridden by subclasses to provide specific relations creation logic.
        """
        return []

    def create_ui_model(
        self,
        element: dict[str, Any],
        path: list[str],
    ) -> dict[str, Any]:
        """Create a UI model for the data type.

        This method should be overridden by subclasses to provide specific UI model creation logic.
        """
        # replace array items:
        # a,[],b => a,b
        # a, [], b, [] => a, b, item
        if not path:
            return {}
        replaced_arrays = [x for x in path[:-1] if x is not ARRAY_ITEM_PATH]
        if path[-1] is ARRAY_ITEM_PATH:
            # if the last element is ARRAY_ITEM_PATH, we replace it with "item"
            replaced_arrays.append("item")
        else:
            replaced_arrays.append(path[-1])

        ret: dict[str, Any] = {
            "help": (element.get("help", {"und": ""})),
            "label": (element.get("label", {"und": replaced_arrays[-1]})),
            "hint": (element.get("hint", {"und": ""})),
        }
        if element.get("required"):
            ret["required"] = True

        if "input" in element:
            ret["input"] = element["input"]
        else:
            ret["input"] = self._registry.get_type(element).TYPE

        return ret


if TYPE_CHECKING:
    FacetMixinBase = DataType
else:
    FacetMixinBase = object


class FacetMixin(FacetMixinBase):
    """Mixin for basic facet generation."""

    def get_facet(
        self,
        path: str,
        element: dict[str, Any],
        nested_facets: list[Any],
        facets: dict[str, list],
        path_suffix: str = "",
    ) -> Any:
        """Create facets for the data type."""
        if element.get("searchable", True):
            return get_basic_facet(
                facets=facets,
                facet_def=element.get("facet-def"),
                facet_name=path,
                facet_path=path + path_suffix,
                content=nested_facets,
                facet_class=self.facet_name,
                facet_kwargs=self._get_facet_kwargs(path, element),
                label=element.get("label"),
            )
        return facets

    def _get_facet_kwargs(
        self,
        path: str,
        element: dict[str, Any],
    ) -> dict[str, Any]:
        """Get extra kwargs for facet constructor."""
        _, _ = path, element
        return {}
