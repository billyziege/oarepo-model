#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see https://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Tests for deferred pid_field resolution in pid-relation.

Bug: `_pid_field()` called `obj_or_import_string()` eagerly at model construction
time, causing `ImportError` / `None` when a pid-relation referenced a record
class that had not yet been imported (circular imports, same-module references).

Fix: `_pid_field()` now returns a zero-argument callable; resolution is deferred
to `AddPIDRelation.apply()`, when all modules are guaranteed to be loaded.
"""
from __future__ import annotations

import pytest


class TestPidRelationLazyImport:
    """_pid_field() must return a callable rather than resolving the import
    immediately, so that a model referencing another model can be constructed
    without a circular-import or missing-module error at import time.
    """

    def test_pid_field_returns_callable_for_record_cls(self, datatype_registry):
        """_pid_field() must return a callable even when the module does not exist."""
        element = {
            "type": "pid-relation",
            "keys": ["id"],
            "record_cls": "this.module.does.not.exist:SomeRecord",
        }
        dt = datatype_registry.get_type(element)
        result = dt._pid_field(element, [])
        assert callable(result), (
            "_pid_field() should return a callable (lazy resolver), "
            "not raise ImportError at call time"
        )

    def test_pid_field_returns_callable_for_pid_field(self, datatype_registry):
        """_pid_field() must return a callable when pid_field string is given."""
        element = {
            "type": "pid-relation",
            "keys": ["id"],
            "pid_field": "this.module.does.not.exist:get_pid",
        }
        dt = datatype_registry.get_type(element)
        result = dt._pid_field(element, [])
        assert callable(result), (
            "_pid_field() should return a callable for pid_field strings too"
        )

    def test_pid_field_callable_raises_on_bad_record_cls(self, datatype_registry):
        """The callable returned by _pid_field() must raise when invoked with a
        non-existent module — but only at invocation time, not at _pid_field() time.
        """
        element = {
            "type": "pid-relation",
            "keys": ["id"],
            "record_cls": "this.module.does.not.exist:SomeRecord",
        }
        dt = datatype_registry.get_type(element)
        resolver = dt._pid_field(element, [])
        with pytest.raises(Exception):
            resolver()

    def test_pid_field_raises_without_pid_field_or_record_cls(self, datatype_registry):
        """_pid_field() must raise ValueError immediately when neither
        pid_field nor record_cls is provided — there is nothing to defer.
        """
        element = {
            "type": "pid-relation",
            "keys": ["id"],
        }
        dt = datatype_registry.get_type(element)
        with pytest.raises(ValueError, match="Either 'pid_field' or 'record_cls'"):
            dt._pid_field(element, [])

    def test_create_relations_does_not_import_at_call_time(self, datatype_registry):
        """create_relations() must complete without raising even when record_cls
        points to a non-existent module, because the import is deferred.
        """
        element = {
            "type": "pid-relation",
            "keys": ["id", "metadata.title"],
            "record_cls": "this.module.does.not.exist:SomeRecord",
        }
        dt = datatype_registry.get_type(element)
        customizations = dt.create_relations(element, [("my_field", element)])
        assert len(customizations) == 1

    def test_add_pid_relation_stores_callable(self, datatype_registry):
        """AddPIDRelation must store the callable so that apply() can resolve it."""
        from oarepo_model.customizations.high_level.add_pid_relation import AddPIDRelation

        sentinel = object()

        def lazy_resolver():
            return sentinel

        relation = AddPIDRelation(
            name="my_field",
            path=["my_field"],
            keys=["id"],
            pid_field=lazy_resolver,
        )
        assert relation.pid_field is lazy_resolver

    def test_add_pid_relation_accepts_direct_value_for_backward_compat(self, datatype_registry):
        """AddPIDRelation must also accept a pre-resolved PIDFieldContext value
        (not callable) for backward compatibility.
        """
        from oarepo_model.customizations.high_level.add_pid_relation import AddPIDRelation

        sentinel = object()
        relation = AddPIDRelation(
            name="my_field",
            path=["my_field"],
            keys=["id"],
            pid_field=sentinel,
        )
        assert relation.pid_field is sentinel
