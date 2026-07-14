#
# Copyright (c) 2026 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""High-level customization for setting models' synthetic metadata."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from ..base import Customization

if TYPE_CHECKING:
    from oarepo_model.builder import InvenioModelBuilder
    from oarepo_model.model import InvenioModel


class SetSyntheticMetadata(Customization):
    """Customization to add synthetic metadata to the model."""

    modifies = ("synthetic_metadata",)

    def __init__(self, **set_fns: Any):
        """Initialize the synthetic_metadata customization."""
        super().__init__("synthetic_metadata")
        self._set_fns = set_fns

    @override
    def apply(self, builder: InvenioModelBuilder, model: InvenioModel) -> None:
        s = builder.get_dictionary("synthetic_metadata")
        for key, value in self._set_fns.items():
            s[key] = value
