#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Data type for PID-based record relations.

This module provides the PIDRelation data type for creating relationships
between records using persistent identifiers (PIDs). It extends the ObjectDataType
to handle record references with configurable keys, PID fields, and caching
mechanisms. The data type automatically generates the necessary relation
customizations for the model builder.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast, override

import marshmallow
from invenio_base.utils import obj_or_import_string

from oarepo_model.customizations.high_level.add_pid_relation import (
    ARRAY_PATH_ITEM,
    AddPIDRelation,
)

from .collections import ObjectDataType

if TYPE_CHECKING:
    from collections.abc import Callable

    from invenio_records_resources.records.systemfields.pid import (
        PIDFieldContext,
    )

    from oarepo_model.customizations.base import Customization


class PIDRelation(ObjectDataType):
    """Relation to another record using a PID.

    Usage:
    ```yaml
    a:
        type: pid-relation
        keys:
        - id
        - metadata.title:
            type: i18nstr
        record_cls: "my_other_model.records:record" or class   (not required if pid_field is provided)
        pid_field: "my_module:pid_field_getter" or PIDField instance (not required if record_cls is provided)
        cache_key: "my_cache_key" (optional, used for caching the resolved record)
    ```
    """

    TYPE = "pid-relation"

    marshmallow_field_class = marshmallow.fields.Nested

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

    def _get_properties(self, element: dict[str, Any]) -> dict[str, Any]:
        if "properties" in element:
            if not isinstance(element["properties"], dict):
                raise TypeError(
                    f"Expected 'properties' to be a dict, got {type(element['properties'])}.",
                )
            return cast("dict[str, Any]", element["properties"])
        ret: dict[str, Any] = {}
        for key in element["keys"]:
            if isinstance(key, str):
                set_key_model(ret, key, {"type": "keyword"})
            elif isinstance(key, dict):
                for k, v in key.items():
                    set_key_model(ret, k, v)
            else:
                raise TypeError(f"Invalid key type: {type(key)}")
        # if 'id' is not in keys, add it as a keyword field
        if "id" not in ret:
            ret["id"] = {"type": "keyword"}
        # if @v is not in keys, add it as a keyword field, set marshmallow as dump only
        if "@v" not in ret:
            ret["@v"] = {"type": "keyword", "skip_marshmallow": True}
        return ret

    @override
    def create_relations(
        self,
        element: dict[str, Any],
        path: list[tuple[str, dict[str, Any]]],
    ) -> list[Customization]:
        relation_path = self._relation_path(element, path)
        relation_name = self._relation_name(element, path)
        pid_field = self._pid_field(element, path)
        cache_key = self._cache_key(element, path)
        key_names = self._key_names(element, path)

        relations: list[Customization] = [
            AddPIDRelation(
                name=relation_name,
                path=relation_path,
                keys=key_names,
                pid_field=pid_field,
                cache_key=cache_key,
                **element.get("relation_field_kwargs", {}),
            ),
        ]

        for prop_name, prop in self._get_properties(element).items():
            relations.extend(
                self._registry.get_type(prop).create_relations(
                    prop,
                    [*path, (prop_name, prop)],
                ),
            )

        return relations

    def _relation_path(
        self,
        element: dict[str, Any],  # noqa: ARG002 for overriding
        path: list[tuple[str, dict[str, Any]]],
    ) -> list:
        """Get the relation path for the PID relation."""
        relation_path: list[str | type[ARRAY_PATH_ITEM]] = []
        for pth in path:
            if pth[0] == "":
                relation_path.append(ARRAY_PATH_ITEM)
            else:
                relation_path.append(pth[0])
        return relation_path

    def _relation_name(
        self,
        element: dict[str, Any],
        path: list[tuple[str, dict[str, Any]]],
    ) -> str:
        relation_path = self._relation_path(element, path)
        return ".".join(str(k) for k in relation_path if k is not ARRAY_PATH_ITEM)

    def _pid_field(
        self,
        element: dict[str, Any],
        path: list[tuple[str, dict[str, Any]]],  # noqa: ARG002 for overriding
    ) -> Callable[[], PIDFieldContext]:
        """Return a lazy callable that resolves the PID field on first use.

        Deferring the import to apply()-time avoids build failures caused by
        circular imports or modules that are not yet on sys.path when the model
        file is first loaded.
        """
        if "pid_field" in element:
            raw = element["pid_field"]

            def resolve_pid_field(_raw: Any = raw, _element: Any = element) -> PIDFieldContext:
                pidf = cast(
                    "Callable[[dict[str, Any]], PIDFieldContext]",
                    obj_or_import_string(_raw),
                )
                if pidf is None or not callable(pidf):
                    raise ValueError(
                        f"PID field {_raw!r} could not be imported.",
                    )
                return pidf(_element)

            return resolve_pid_field

        if "record_cls" in element:
            raw = element["record_cls"]

            def resolve_record_cls(_raw: Any = raw) -> PIDFieldContext:
                rec = obj_or_import_string(_raw)
                if rec is None or not hasattr(rec, "pid"):
                    raise ValueError(
                        f"Record class {_raw!r} does not have a 'pid' attribute.",
                    )
                return rec.pid

            return resolve_record_cls

        raise ValueError(
            "Either 'pid_field' or 'record_cls' must be provided in the pid-relation element.",
        )

    def _cache_key(
        self,
        element: dict[str, Any],
        path: list[tuple[str, dict[str, Any]]],  # noqa: ARG002 for overriding
    ) -> str | None:
        return element.get("cache_key")

    def _key_names(
        self,
        element: dict[str, Any],
        path: list[tuple[str, dict[str, Any]]],  # noqa: ARG002 for overriding
    ) -> list[str]:
        keys = set()
        for key in element.get("keys", []):
            if isinstance(key, str):
                keys.add(key)
            elif isinstance(key, dict):
                keys.update(key.keys())
            else:
                raise TypeError(f"Invalid key type: {type(key)}")
        return list(keys)


def set_key_model(properties: dict[str, Any], key: str, value: Any) -> None:
    """Set a key-value pair in the properties dictionary."""
    parts = key.split(".")
    current = properties
    for part in parts[:-1]:
        if part not in current:
            current[part] = {
                "type": "object",
                "properties": {},
            }
        current = current[part]["properties"]
    current[parts[-1]] = value
