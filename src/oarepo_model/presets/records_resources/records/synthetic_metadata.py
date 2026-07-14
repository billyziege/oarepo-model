#
# Copyright (c) 2026 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Preset for configuring synthetic metadata."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Self, overload, override

from invenio_records.systemfields import DictField
from wrapt import ObjectProxy

from oarepo_model.customizations import (
    AddDictionary,
    Customization,
)
from oarepo_model.presets import Preset

if TYPE_CHECKING:
    from collections.abc import Callable, Generator

    from invenio_records.api import Record

    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class MetadataProxy(ObjectProxy):
    """Object proxy that allows to add synthetic metadata.

    The data are returned only through direct substribt access, otherwise the object is treated as a dict without them.
    This is done to avoid modification to the original metadata, ie. so the synthetic data are not dumped into
    the database.
    """

    def __init__(self, wrapped: dict[str, Any], synthetic: dict[str, Callable[[dict[str, Any]], Any]] | None = None):
        """Construct."""
        super().__init__(wrapped)
        self._self_synthetic = synthetic or {}

    def __getitem__(self, key: str) -> Any:
        """Return synthetic metadata if available."""
        if key not in self.__wrapped__ and key in self._self_synthetic:
            fn = self._self_synthetic[key]
            return fn(self.__wrapped__)
        return super().__getitem__(key)


class MetadataField(DictField):
    """Dictionary field supporting synthetic metadata."""

    def __init__(self, *args: Any, synthetic: dict[str, Callable[[dict[str, Any]], Any]], **kwargs: Any):
        """Construct."""
        super().__init__(*args, **kwargs)
        self.synthetic = synthetic

    @overload
    def __get__(self, record: None, owner: type[Record]) -> Self: ...
    @overload
    def __get__(self, record: Record, owner: type[Record]) -> MetadataProxy: ...

    @override
    def __get__(self, record, owner):
        ret = super().__get__(record, owner)
        if ret is None:
            ret = {}
        if isinstance(ret, dict):
            ret = MetadataProxy(ret, self.synthetic)
        return ret


class SyntheticMetadataPreset(Preset):
    """Preset initializing synthetic metadata dictionary."""

    provides = ("synthetic_metadata",)

    @override
    def apply(
        self,
        builder: InvenioModelBuilder,
        model: InvenioModel,
        dependencies: dict[str, Any],
    ) -> Generator[Customization]:

        yield AddDictionary(
            "synthetic_metadata",
            default={},
        )
