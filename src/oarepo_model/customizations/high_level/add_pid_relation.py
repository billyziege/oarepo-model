#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""High-level customization for adding PID relations to models.

This module provides the AddPIDRelation customization that creates appropriate
PID relation system fields based on the path structure. It supports simple
relations, list relations, and nested list relations by analyzing the presence
and position of array items in the relation path.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from invenio_records_resources.records.systemfields import (
    PIDListRelation,
    PIDNestedListRelation,
    PIDRelation,
)
from oarepo_runtime.records.systemfields.relations import PIDArbitraryNestedListRelation

from ..base import Customization

if TYPE_CHECKING:
    from collections.abc import Callable

    from invenio_records_resources.records.systemfields.pid import PIDFieldContext

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class ARRAY_PATH_ITEM:  # noqa: N801
    """Marker for array items in the path.

    This class is used to indicate that a part of the path is an array item.
    It is used to differentiate between simple relations and list relations.
    """


class AddPIDRelation(Customization):
    """Customization to add PID relations to the model."""

    def __init__(
        self,
        name: str,
        path: list[str | type[ARRAY_PATH_ITEM]],
        keys: list[str],
        pid_field: PIDFieldContext | Callable[[], PIDFieldContext],
        cache_key: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the AddPIDRelation customization.

        :param path: The path to the relation.
        :param keys: The keys for the relation.
        """
        super().__init__("add_pid_relation")
        self.name = name
        self.path = path
        self.keys = keys
        self.pid_field = pid_field
        self.cache_key = cache_key
        self.kwargs = kwargs

    @override
    def apply(self, builder: InvenioModelBuilder, model: InvenioModel) -> None:
        relations = builder.get_dictionary("relations")
        array_count = self.path.count(ARRAY_PATH_ITEM)

        relation_field, array_paths = self._merge_paths_between_arrays()

        # Resolve lazily — all modules are loaded by the time apply() is called,
        # so circular imports and missing modules are no longer a concern.
        pid_field = self.pid_field() if callable(self.pid_field) else self.pid_field

        match array_count:
            case 0:
                relations[self.name] = PIDRelation(
                    relation_field,
                    keys=self.keys,
                    pid_field=pid_field,
                    cache_key=self.cache_key,
                    **self.kwargs,
                )
            case 1:
                # If the last element is an array, we create a PIDListRelation
                relations[self.name] = PIDListRelation(
                    array_paths[0],
                    keys=self.keys,
                    pid_field=pid_field,
                    cache_key=self.cache_key,
                    relation_field=relation_field,
                    **self.kwargs,
                )
            case 2:
                if relation_field:
                    # invenio can not handle 2 arrays with a relation field at the end
                    # for that we use the arbitrary nested list relation that can do it
                    # albeit with a bit less efficiency
                    relations[self.name] = PIDArbitraryNestedListRelation(
                        array_paths=array_paths,
                        relation_field=relation_field,
                        keys=self.keys,
                        pid_field=pid_field,
                        cache_key=self.cache_key,
                        **self.kwargs,
                    )
                else:
                    relations[self.name] = PIDNestedListRelation(
                        array_paths[0],
                        relation_field=array_paths[1],
                        keys=self.keys,
                        pid_field=pid_field,
                        cache_key=self.cache_key,
                        **self.kwargs,
                    )
            case _:
                relations[self.name] = PIDArbitraryNestedListRelation(
                    array_paths=array_paths,
                    relation_field=relation_field,
                    keys=self.keys,
                    pid_field=pid_field,
                    cache_key=self.cache_key,
                    **self.kwargs,
                )

    def _merge_paths_between_arrays(self) -> tuple[str | None, list[str]]:
        """Merge path segments between array markers.

        This method processes the path to identify segments between array markers
        and merges them into dot-separated strings. It also determines the relation
        field (the segment after the last array marker) if it exists.
        """
        merged_paths_with_array_markers: list[Any] = []
        joined: list[str] = []
        for x in self.path:
            if isinstance(x, str):
                joined.append(x)
            else:
                if joined:
                    merged_paths_with_array_markers.append(".".join(joined))
                    joined = []
                merged_paths_with_array_markers.append(ARRAY_PATH_ITEM)
        if joined:
            merged_paths_with_array_markers.append(".".join(joined))

        # pop the relation field if the last item is not an array
        relation_field = (
            None if merged_paths_with_array_markers[-1] is ARRAY_PATH_ITEM else merged_paths_with_array_markers.pop()
        )

        # filter out array markers
        array_paths = [x for x in merged_paths_with_array_markers if x is not ARRAY_PATH_ITEM]

        return relation_field, array_paths
