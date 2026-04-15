#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Collection data types for OARepo models.

This module provides collection-based data types including arrays, objects,
nested structures, and dynamic objects for use in OARepo models.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any, override

import marshmallow
from invenio_base.utils import obj_or_import_string
from invenio_i18n import gettext as _

from oarepo_model.utils import MultiFormatField, convert_to_python_identifier

from .base import ARRAY_ITEM_PATH, DataType, FacetMixin

if TYPE_CHECKING:
    from collections.abc import Mapping

    from oarepo_model.customizations.base import Customization


class ObjectDataType(DataType):
    """A data type representing an object in the Oarepo model.

    This class can be extended to create custom object data types.
    """

    TYPE = "object"

    marshmallow_field_class = marshmallow.fields.Nested
    jsonschema_type = "object"
    mapping_type = "object"

    def _get_properties(self, element: dict[str, Any]) -> dict[str, Any]:
        """Get the properties for the object data type.

        This method can be overridden by subclasses to provide specific properties logic.
        """
        if "properties" not in element:
            raise ValueError(f"Element must contain 'properties' key. Got {element}")  # pragma: no cover
        if not isinstance(element["properties"], dict):
            raise TypeError(
                "Element 'properties' must be a dictionary.",
            )
        return element["properties"]

    def create_marshmallow_schema(
        self,
        element: dict[str, Any],
    ) -> type[marshmallow.Schema]:
        """Create a Marshmallow schema for the object data type.

        This method should be overridden by subclasses to provide specific schema creation logic.
        """
        if "marshmallow_schema_class" in element:
            # if marshmallow_schema_class is specified, use it directly
            imported = obj_or_import_string(element["marshmallow_schema_class"])
            if not isinstance(imported, type) or not issubclass(imported, marshmallow.Schema):
                raise ValueError(
                    f"marshmallow_schema_class {element['marshmallow_schema_class']} "
                    "must be a subclass of marshmallow.Schema",
                )
            return imported

        properties = self._get_properties(element)

        # TODO: create marshmallow field should pass extra arguments such attribute and data_key
        properties_fields: dict[str, Any] = {
            convert_to_python_identifier(key): self._registry.get_type(
                value,
            ).create_marshmallow_field(key, value)
            for key, value in properties.items()
            if not value.get("skip_marshmallow", False)
        }

        class Meta:
            unknown = marshmallow.RAISE

        properties_fields["Meta"] = Meta
        return type(self.name, (marshmallow.Schema,), properties_fields)

    def create_ui_marshmallow_schema(
        self,
        element: dict[str, Any],
    ) -> type[marshmallow.Schema]:
        """Create a Marshmallow UI schema for the object data type.

        This method should be overridden by subclasses to provide specific schema creation logic.
        """
        if "ui_marshmallow_schema_class" in element:
            # if marshmallow_schema_class is specified, use it directly
            imported = obj_or_import_string(element["ui_marshmallow_schema_class"])
            if not isinstance(imported, type) or not issubclass(imported, marshmallow.Schema):
                raise ValueError(
                    f"ui_marshmallow_schema_class {element['ui_marshmallow_schema_class']} "
                    "must be a subclass of marshmallow.Schema",
                )
            return imported

        properties = self._get_properties(element)

        properties_fields: dict[str, Any] = {}

        for key, value in properties.items():
            properties_fields.update(
                self._registry.get_type(value).create_ui_marshmallow_fields(key, value),
            )

        class Meta:
            unknown = marshmallow.RAISE

        properties_fields["Meta"] = Meta
        return type(self.name, (marshmallow.Schema,), properties_fields)

    def get_facet(
        self,
        path: str,
        element: dict[str, Any],
        nested_facets: list[Any],
        facets: dict[str, list],
        path_suffix: str = "",
    ) -> Any:
        """Create facets for the data type."""
        _ = path_suffix  # path suffix is not used for objects
        if "properties" in element:
            properties = self._get_properties(element)
            for key, value in properties.items():
                if path == "":
                    _path = key
                elif path.endswith(key):
                    _path = path
                else:
                    _path = path + "." + key
                facets.update(self._registry.get_type(value).get_facet(_path, value, nested_facets, facets))

        return facets

    def create_ui_marshmallow_fields(
        self,
        field_name: str,
        element: dict[str, Any],
    ) -> dict[str, marshmallow.fields.Field]:
        """Create a Marshmallow UI fields for the object data type.

        This method should be overridden by subclasses to provide specific schema creation logic.
        """
        if element.get("ui_marshmallow_field") is not None:
            # if marshmallow_field is specified, use it directly
            ui_marshmallow_field = obj_or_import_string(element["ui_marshmallow_field"])
            if ui_marshmallow_field is None or not isinstance(ui_marshmallow_field, marshmallow.fields.Field):
                raise TypeError(
                    f"ui_marshmallow_field must be an instance of marshmallow.fields.Field, got {ui_marshmallow_field}",
                )
            return {
                field_name: ui_marshmallow_field,
            }
        field_class = self._get_ui_marshmallow_field_class(field_name, element) or marshmallow.fields.Nested
        return {
            field_name: field_class(
                self.create_ui_marshmallow_schema(element),
            ),
        }

    @override
    def _get_marshmallow_field_args(
        self,
        field_name: str,
        element: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "nested": self.create_marshmallow_schema(element),
            **super()._get_marshmallow_field_args(field_name, element),
        }

    @override
    def create_json_schema(self, element: dict[str, Any]) -> dict[str, Any]:
        properties = self._get_properties(element)
        return {
            **super().create_json_schema(element),
            "unevaluatedProperties": False,
            "properties": {
                key: self._registry.get_type(value).create_json_schema(value) for key, value in properties.items()
            },
        }

    @override
    def create_mapping(self, element: dict[str, Any]) -> dict[str, Any]:
        properties = self._get_properties(element)
        return {
            **super().create_mapping(element),
            "dynamic": "strict",
            "properties": {
                key: self._registry.get_type(value).create_mapping(value) for key, value in properties.items()
            },
        }

    @override
    def create_relations(
        self,
        element: dict[str, Any],
        path: list[tuple[str, dict[str, Any]]],
    ) -> list[Customization]:
        """Iterate through the properties of this object and create relations."""
        ret = []
        for key, value in self._get_properties(element).items():
            ret.extend(
                self._registry.get_type(value).create_relations(
                    value,
                    [*path, (key, value)],
                ),
            )
        return ret

    @override
    def create_ui_model(
        self,
        element: dict[str, Any],
        path: list[str],
    ) -> dict[str, Any]:
        """Create a UI model for the data type.

        This method should be overridden by subclasses to provide specific UI model creation logic.
        """
        ret = super().create_ui_model(element, path)
        ret["children"] = {
            key: self._registry.get_type(value).create_ui_model(value, [*path, key])
            for key, value in self._get_properties(element).items()
        }
        return ret


class NestedDataType(ObjectDataType):
    """A data type representing a "nested" in the Oarepo model."""

    TYPE = "nested"
    mapping_type = "nested"

    def get_facet(
        self,
        path: str,
        element: dict[str, Any],
        nested_facets: list[Any],
        facets: dict[str, list],
        path_suffix: str = "",
    ) -> Any:
        """Create facets for the data type."""
        _ = path_suffix  # path suffix is not used for nested objects
        if "properties" in element:
            properties = self._get_properties(element)
            for key, value in properties.items():
                _path = path if path.endswith(key) else f"{path}.{key}"

                facets.update(
                    self._registry.get_type(value).get_facet(
                        _path,
                        value,
                        nested_facets=[
                            *nested_facets,
                            {
                                "facet": "oarepo_runtime.services.facets.nested_facet.NestedLabeledFacet",
                                "path": path,
                            },
                        ],
                        facets=facets,
                    )
                )
        return facets


def unique_validator(value: list[Any]) -> None:
    """Validate that the array does not contain duplicates."""
    values_as_strings = [json.dumps(item, sort_keys=True) for item in value]
    # get duplicates
    duplicates = {item for item in values_as_strings if values_as_strings.count(item) > 1}
    if duplicates:
        raise marshmallow.ValidationError(
            _("Array contains duplicates: {}").format(", ".join(duplicates)),
        )


class ArrayDataType(FacetMixin, DataType):
    """A data type representing an array in the Oarepo model.

    This class can be extended to create custom array data types.
    """

    TYPE = "array"

    jsonschema_type = "array"
    marshmallow_field_class = marshmallow.fields.List

    @override
    def _get_marshmallow_field_args(
        self,
        field_name: str,
        element: dict[str, Any],
    ) -> dict[str, Any]:
        if "items" not in element:
            raise ValueError("Element must contain 'items' key.")
        ret = super()._get_marshmallow_field_args(field_name, element)
        ret["cls_or_instance"] = self._registry.get_type(
            element["items"],
        ).create_marshmallow_field(ARRAY_ITEM_PATH, element["items"])
        if "min_items" in element or "max_items" in element:
            ret.setdefault("validate", []).append(
                marshmallow.validate.Length(
                    min=element.get("min_items"),
                    max=element.get("max_items"),
                ),
            )
        if element.get("unique_items"):
            ret.setdefault("validate", []).append(unique_validator)
        return ret

    @override
    def create_ui_marshmallow_fields(
        self,
        field_name: str,
        element: dict[str, Any],
    ) -> dict[str, marshmallow.fields.Field]:
        """Create a Marshmallow UI fields for the array data type.

        This method should be overridden by subclasses to provide specific schema creation logic.
        """
        if element.get("ui_marshmallow_field") is not None:
            # if marshmallow_field is specified, use it directly
            ui_fld = obj_or_import_string(element["ui_marshmallow_field"])
            if ui_fld is None or not isinstance(ui_fld, marshmallow.fields.Field):
                raise TypeError(
                    f"ui_marshmallow_field must be an instance of marshmallow.fields.Field, got {ui_fld}",
                )
            return {
                field_name: ui_fld,
            }

        # retrieve formatting options (e.g. for the date items type -> long, short etc.)
        items_fields = self._registry.get_type(
            element["items"],
        ).create_ui_marshmallow_fields("item", element["items"])
        # no transformations
        if not items_fields:
            return {}

        # if there is only one field, just use it otherwise create a multi-format field
        field = next(iter(items_fields.values())) if len(items_fields) == 1 else MultiFormatField(items_fields)

        # get representation of a marshmallow field
        field_class = self._get_ui_marshmallow_field_class(field_name, element) or marshmallow.fields.List
        return {field_name: field_class(field)}

    @override
    def create_json_schema(self, element: dict[str, Any]) -> dict[str, Any]:
        return {
            **super().create_json_schema(element),
            "items": self._registry.get_type(element["items"]).create_json_schema(
                element["items"],
            ),
        }

    @override
    def create_mapping(self, element: dict[str, Any]) -> Mapping[str, Any]:
        # skip the array in mapping
        return self._registry.get_type(element["items"]).create_mapping(
            element["items"],
        )

    @override
    def create_ui_model(
        self,
        element: dict[str, Any],
        path: list[str],
    ) -> dict[str, Any]:
        """Create a UI model for the data type.

        This method should be overridden by subclasses to provide specific UI model creation logic.
        """
        ret = super().create_ui_model(element, path)
        ret["child"] = self._registry.get_type(element["items"]).create_ui_model(
            element["items"],
            [*path, ARRAY_ITEM_PATH],
        )
        if "min_items" in element or "max_items" in element:
            ret["min_items"] = element.get("min_items")
            ret["max_items"] = element.get("max_items")
        if element.get("unique_items"):
            ret["unique_items"] = True
        return ret

    @override
    def create_relations(
        self,
        element: dict[str, Any],
        path: list[tuple[str, dict[str, Any]]],
    ) -> list[Customization]:
        return self._registry.get_type(element["items"]).create_relations(
            element["items"],
            [*path, ("", element)],
        )

    def get_facet(
        self,
        path: str,
        element: dict[str, Any],
        nested_facets: list[Any],
        facets: dict[str, list],
        path_suffix: str = "",
    ) -> Any:
        """Create facets for the data type."""
        _ = path_suffix  # path suffix is not used for arrays
        path = path.removesuffix("[]")
        value = element.get("items", element)
        facets.update(self._registry.get_type(value).get_facet(path, value, nested_facets, facets))
        return facets


class PermissiveSchema(marshmallow.Schema):
    """A permissive schema that allows any properties."""

    class Meta:
        """Meta class for PermissiveSchema."""

        unknown = marshmallow.INCLUDE


class DynamicObjectDataType(ObjectDataType):
    """A data type for multilingual dictionaries.

    Their serialization is:
    {
        "en": "English text",
        "fi": "Finnish text",
        ...
    }
    """

    TYPE = "dynamic-object"

    @override
    def _get_properties(self, element: dict[str, Any]) -> dict[str, Any]:
        """Get properties for the data type."""
        return {}  # dynamic object has no explicit properties

    @override
    def create_marshmallow_field(
        self,
        field_name: str,
        element: dict[str, Any],
    ) -> marshmallow.fields.Field:
        """Return a Raw field that passes arbitrary JSON through unchanged on both load and dump."""
        # Use the base DataType args, not ObjectDataType's override, because
        # ObjectDataType._get_marshmallow_field_args injects 'nested' which is
        # only meaningful for Nested fields and causes a marshmallow warning on Raw.
        from .base import DataType
        return marshmallow.fields.Raw(
            **DataType._get_marshmallow_field_args(self, field_name, element),
        )

    @override
    def create_marshmallow_schema(
        self,
        element: dict[str, Any],
    ) -> type[marshmallow.Schema]:
        return PermissiveSchema

    @override
    def create_ui_marshmallow_fields(self, field_name: str, element: dict[str, Any]) -> dict[str, Any]:
        return {}

    @override
    def create_json_schema(self, element: dict[str, Any]) -> dict[str, Any]:
        return {"type": "object", "additionalProperties": True}

    @override
    def create_mapping(self, element: dict[str, Any]) -> dict[str, Any]:
        return {"type": "object", "dynamic": "true"}

    @override
    def create_relations(
        self,
        element: dict[str, Any],
        path: list[tuple[str, dict[str, Any]]],
    ) -> list[Customization]:
        # can not get relations for dynamic objects
        return []
