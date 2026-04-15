#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Data type for polymorphic schemas with discriminator fields.

This module provides the PolymorphicDataType class for handling fields that can
be one of several different types based on a discriminator field. It includes
the PolymorphicField Marshmallow field for runtime type resolution and validation.
The data type supports 'oneof' schemas where each variant specifies a discriminator
value and corresponding schema type.
"""

from __future__ import annotations

from typing import Any, override

import marshmallow as ma
from deepmerge import always_merger
from invenio_base.utils import obj_or_import_string
from marshmallow.utils import get_value
from marshmallow.utils import (
    missing as missing_,
)

from .base import DataType


class PolymorphicDataType(DataType):
    """Data type for handling polymorphic schemas with discriminator fields.

    This allows for fields that can be one of several different types based on a discriminator field.

    Supports schemas with a 'oneof' array where each item specifies a discriminator value
    and corresponding schema type. The discriminator field determines which schema variant
    to use for validation and serialization.

    Example:
    This schema will support two types of items (person and organization):
       {
           "type": "polymorphic",
           "discriminator": "type",
           "oneof": [
               {"discriminator": "person", "type": "Person"},
               {"discriminator": "organization", "type": "Organization"}
           ]
       }

    Input will be:
    {
        field_name : {"type": "person", person_fields...}
    } or
    {
        field_name : {"type": "organization", organization_fields...}
    }

    """

    TYPE = "polymorphic"

    @override
    def create_marshmallow_field(
        self,
        field_name: str,
        element: dict[str, Any],
    ) -> ma.fields.Field:
        """Create a Marshmallow field for polymorphic data type.

        Uses OneOf field with different schemas based on discriminator.
        """
        if element.get("marshmallow_field") is not None:
            mf = obj_or_import_string(element["marshmallow_field"])
            if mf is None or not isinstance(mf, ma.fields.Field):
                raise TypeError(
                    f"marshmallow_field must be an instance of marshmallow.fields.Field, got {mf}",
                )
            return mf

        # get discriminator field name
        discriminator = element.get("discriminator", "type")

        # create a custom polymorphic field that distinguishes what schema to use
        return PolymorphicField(
            discriminator=discriminator,
            alternatives=self._create_schema_fields(field_name, element),
            **self._get_marshmallow_field_args(field_name, element),
        )

    def _create_schema_fields(
        self,
        field_name: str,
        element: dict[str, Any],
    ) -> dict[str, ma.fields.Field]:
        """Create marshmallow fields for each schema variant."""
        schema_fields = {}
        oneof_schemas = element.get("oneof", [])

        for oneof_item in oneof_schemas:
            # get discriminator value (e.g. person) and schema for that value (e.g. Person)
            discriminator_value = oneof_item.get("discriminator")
            schema_type = oneof_item.get("type")

            if discriminator_value and schema_type:
                # get class for this schema type
                datatype = self._registry.get_type(schema_type)

                # create a marshmallow field and save it
                schema_fields[discriminator_value] = datatype.create_marshmallow_field(
                    field_name=field_name,
                    element=oneof_item,
                )

        return schema_fields

    @override
    def create_ui_marshmallow_fields(
        self,
        field_name: str,
        element: dict[str, Any],
    ) -> dict[str, ma.fields.Field]:
        alternative_fields = {}
        discriminator = element.get("discriminator", "type")
        oneof_schemas = element.get("oneof", [])

        # iterate through each variant
        for oneof_item in oneof_schemas:
            # get its disciminator and schema type
            discriminator_value = oneof_item.get("discriminator")
            schema_type = oneof_item.get("type")

            if discriminator_value and schema_type:
                # get class for that specific datatype
                datatype = self._registry.get_type(schema_type)

                # get UI fields from that datatype, where attribute is disciminator value
                ui_fields = datatype.create_ui_marshmallow_fields(
                    field_name=field_name,
                    element=oneof_item,
                )
                if len(ui_fields) != 1:
                    raise NotImplementedError(
                        "Current version can only handle 1 UI field in polymorphic type!",
                    )

                alternative_fields[discriminator_value] = next(iter(ui_fields.values()))

        # return custom marshmallow field that distinguishes what schema to use
        field_class = self._get_ui_marshmallow_field_class(field_name, element) or PolymorphicField
        return {
            field_name: field_class(
                discriminator=discriminator,
                alternatives=alternative_fields,
                preserve_discriminator=False,
            ),
        }

    @override
    def create_json_schema(self, element: dict[str, Any]) -> dict[str, Any]:
        """Create JSON schema for polymorphic type using oneOf."""
        discriminator = element.get("discriminator", "type")
        oneof_schemas = element.get("oneof", [])

        json_one_of_schemas = []

        # iterate through each variant
        for oneof_item in oneof_schemas:
            # get its disciminator and schema type
            discriminator_value = oneof_item.get("discriminator")
            schema_type = oneof_item.get("type")

            if discriminator_value and schema_type:
                # get datatype class and generate json schema from it
                datatype = self._registry.get_type(schema_type)
                child_jsonschema = datatype.create_json_schema(oneof_item)

                if "properties" not in child_jsonschema:
                    child_jsonschema = dict(child_jsonschema)  # make a copy to avoid modifying the original
                    child_jsonschema["properties"] = {}

                # only 1 value is allowed in this field (e.g. person or organization)
                child_jsonschema["properties"][discriminator] = {
                    "type": "string",
                    "const": discriminator_value,
                }

                # discriminator is a required field
                if "required" not in child_jsonschema:
                    child_jsonschema = dict(child_jsonschema)  # make a copy to avoid modifying the original
                    child_jsonschema["required"] = []
                if discriminator not in child_jsonschema["required"]:
                    child_jsonschema["required"].append(discriminator)

                json_one_of_schemas.append(child_jsonschema)

        return {
            "oneOf": json_one_of_schemas,
        }

    @override
    def create_mapping(self, element: dict[str, Any]) -> dict[str, Any]:
        """Create a mapping for the data type.

        Uses object type with properties from all possible schemas.
        """
        discriminator = element.get("discriminator", "type")
        oneof_schemas = element.get("oneof", [])

        all_properties = {discriminator: {"type": "keyword"}}

        # iterate through each variant
        for oneof_item in oneof_schemas:
            # get its discriminator and schema type
            discriminator_value = oneof_item.get("discriminator")
            schema_type = oneof_item.get("type")

            if discriminator_value and schema_type:
                # get datatype class and generate mapping from it
                datatype = self._registry.get_type(schema_type)
                child_mapping = datatype.create_mapping(oneof_item)

                # dump all properties from all variants in 1 dictionary
                if "properties" in child_mapping:
                    all_properties = always_merger.merge(
                        all_properties,
                        child_mapping["properties"],
                    )

        return {"type": "object", "properties": all_properties}


class PolymorphicField(ma.fields.Field):
    """Custom marshmallow field class that supports handling polymorphic fields."""

    def __init__(
        self,
        discriminator: str,
        alternatives: dict[str, ma.fields.Field],
        *args: Any,
        preserve_discriminator: bool = True,
        **kwargs: Any,
    ):
        """Initialize a PolymorphicField for handling discriminated union types.

        :param discriminator:
            The field name used to determine which schema variant to use.
            Defaults to "type".
        :param alternatives:
            A mapping from discriminator values (e.g. person/organization)
            to marshmallow field instances. Each field handles validation and
            serialization for its corresponding object variant. Defaults to empty dict.
        :param preserve_discriminator:
            When True (default), the discriminator key is re-added to the
            serialized output after the sub-schema dumps, ensuring round-trip
            fidelity for data schemas.  Set to False for UI schemas where only
            UI-transformed fields should appear in the output.
        """
        super().__init__(*args, **kwargs)
        self.discriminator = discriminator
        self.alternatives = alternatives
        self.preserve_discriminator = preserve_discriminator

    def get_discriminator_value(self, obj: Any) -> str:
        """Get the discriminator value from the object."""
        val = get_value(
            obj,
            self.discriminator,
        )

        if val is missing_:
            error = self.make_error(key="required")
            error.field_name = self.discriminator
            raise error

        if not isinstance(val, str):
            error = ma.ValidationError("Discriminator value must be a string.")
            error.field_name = self.discriminator
            raise error

        return val

    @override
    def _serialize(self, value: Any, attr: str | None, obj: Any, **kwargs: Any) -> Any:
        """Serialize by choosing correct serializer depending on the discriminator value."""
        if not isinstance(value, dict):
            return value

        discriminator_value = self.get_discriminator_value(value)
        if discriminator_value not in self.alternatives:
            return value

        schema_field = self.alternatives[discriminator_value]
        serialized = schema_field._serialize(  # noqa: SLF001 private access
            value,
            attr,
            obj,
            **kwargs,
        )

        # Re-add the discriminator: the sub-schema only dumps its declared fields
        # and would otherwise silently drop it, breaking round-trips.
        # For UI schemas (preserve_discriminator=False) this step is intentionally
        # skipped — only UI-transformed fields should appear in the output.
        if isinstance(serialized, dict) and self.preserve_discriminator:
            serialized[self.discriminator] = discriminator_value

        return serialized

    @override
    def _deserialize(
        self,
        value: Any,
        attr: str | None,
        data: Any,
        **kwargs: Any,
    ) -> Any:
        """Deserialize by choosing correct deserializer depending on the discriminator value."""
        discriminator_value = self.get_discriminator_value(value)

        if discriminator_value not in self.alternatives:
            raise ma.ValidationError(
                f"Unknown type {discriminator_value!r}. "
                f"Valid types are: {list(self.alternatives)}",
            )

        # Strip the discriminator before handing off to the sub-schema.
        # The sub-schema has unknown=RAISE and does not declare the discriminator
        # field, so passing the full dict causes ValidationError: Unknown field.
        value_without_discriminator = {
            k: v for k, v in value.items() if k != self.discriminator
        }

        schema_field = self.alternatives[discriminator_value]
        result = schema_field._deserialize(  # noqa: SLF001 private access
            value_without_discriminator,
            attr,
            data,
            **kwargs,
        )

        # Put the discriminator back into the deserialized result so that
        # _serialize can find it and round-trips are lossless.
        if isinstance(result, dict):
            result[self.discriminator] = discriminator_value

        return result
