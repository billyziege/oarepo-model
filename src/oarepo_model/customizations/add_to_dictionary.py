#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Customization for adding key-value pairs to dictionaries in the model.

This module provides the AddToDictionary customization that allows adding or
updating key-value pairs in existing dictionaries. It supports both simple
key-value additions and complex merging operations with patch functionality
for updating existing values.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from deepmerge import always_merger

from .base import Customization

if TYPE_CHECKING:
    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class AddToDictionary(Customization):
    """Customization to add a value to a dictionary to the model."""

    def __init__(  # noqa PLR0913
        self,
        dictionary_name: str,
        *values: dict[str, Any],
        key: str | None = None,
        value: Any = None,
        exists_ok: bool = False,
        patch: bool = False,
        override_values: bool = True,
    ) -> None:
        """Initialize the AddDictionary customization.

        :param name: The name of the dictionary to be added.
        :param default: The default value of the dictionary.
        :param exists_ok: Whether to ignore if the dictionary already exists.
        """
        super().__init__(dictionary_name)
        self.key = key
        self.value = value
        self.values = values
        self.exists_ok = exists_ok
        self.patch = patch
        self.override_values = override_values

    @override
    def apply(self, builder: InvenioModelBuilder, model: InvenioModel) -> None:
        d = builder.add_dictionary(self.name, exists_ok=True)
        for value in self.values:
            if self.override_values:
                always_merger.merge(d, value)
            else:
                for k, new_value in value.items():
                    if k not in d:
                        d[k] = new_value
        if self.key is not None:
            if self.key in d and not self.exists_ok:
                if not self.patch:
                    raise ValueError(
                        f"Key '{self.key}' already exists in dictionary '{self.name}'.",
                    )
                d[self.key] = always_merger.merge(d[self.key], self.value)
            else:
                d[self.key] = self.value
