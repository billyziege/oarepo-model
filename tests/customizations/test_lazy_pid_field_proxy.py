#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see https://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Tests for LazyPIDFieldProxy and AddPIDRelation.apply() lazy-wrapping behaviour.

Covers:
  - LazyPIDFieldProxy does NOT call its factory during __init__
  - LazyPIDFieldProxy calls factory on first attribute access
  - LazyPIDFieldProxy calls factory exactly once (result is cached)
  - LazyPIDFieldProxy forwards attribute reads transparently to the resolved object
  - LazyPIDFieldProxy handles the late-binding scenario: factory that would fail
    if called eagerly during model construction succeeds once all modules are loaded
  - AddPIDRelation.apply() wraps a callable pid_field in LazyPIDFieldProxy instead
    of calling it immediately
  - AddPIDRelation.apply() passes a non-callable pid_field through unchanged
"""
from __future__ import annotations

from types import SimpleNamespace

import pytest

from oarepo_model.customizations.high_level.add_pid_relation import (
    ARRAY_PATH_ITEM,
    AddPIDRelation,
    LazyPIDFieldProxy,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class _FakeBuilder:
    """Minimal stand-in for InvenioModelBuilder used to test apply()."""

    def __init__(self):
        self._dicts: dict[str, dict] = {}

    def get_dictionary(self, name: str) -> dict:
        return self._dicts.setdefault(name, {})


# ---------------------------------------------------------------------------
# LazyPIDFieldProxy unit tests
# ---------------------------------------------------------------------------

class TestLazyPIDFieldProxy:
    """LazyPIDFieldProxy must defer factory invocation until first attribute access."""

    def test_factory_not_called_during_init(self):
        """__init__ must NOT invoke the factory."""
        call_log: list[int] = []

        def factory():
            call_log.append(1)
            return SimpleNamespace()

        LazyPIDFieldProxy(factory)
        assert call_log == [], (
            "LazyPIDFieldProxy.__init__ must not call the factory; "
            f"factory was called {len(call_log)} time(s)"
        )

    def test_factory_called_on_first_attribute_access(self):
        """Accessing any attribute for the first time must trigger the factory."""
        call_log: list[int] = []
        resolved = SimpleNamespace(pid_type="recid")

        def factory():
            call_log.append(1)
            return resolved

        proxy = LazyPIDFieldProxy(factory)
        assert call_log == [], "pre-condition: factory not yet called"
        _ = proxy.pid_type
        assert call_log == [1], "factory must be called on first attribute access"

    def test_factory_called_exactly_once(self):
        """Multiple attribute accesses must trigger the factory only once."""
        call_count = 0
        resolved = SimpleNamespace(a=1, b=2, c=3)

        def factory():
            nonlocal call_count
            call_count += 1
            return resolved

        proxy = LazyPIDFieldProxy(factory)
        _ = proxy.a
        _ = proxy.b
        _ = proxy.c
        assert call_count == 1, (
            f"factory must be called exactly once; was called {call_count} time(s)"
        )

    def test_attribute_forwarded_to_resolved_object(self):
        """Attribute reads must return the value from the resolved object."""
        resolved = SimpleNamespace(pid_type="recid", session_merge="no-op", extra=42)
        proxy = LazyPIDFieldProxy(lambda: resolved)
        assert proxy.pid_type == "recid"
        assert proxy.session_merge == "no-op"
        assert proxy.extra == 42

    def test_missing_attribute_raises_attribute_error(self):
        """Accessing a missing attribute must propagate AttributeError from the
        resolved object, not get swallowed by the proxy."""
        resolved = SimpleNamespace(existing="yes")
        proxy = LazyPIDFieldProxy(lambda: resolved)
        with pytest.raises(AttributeError):
            _ = proxy.does_not_exist

    def test_late_binding_simulates_circular_import_scenario(self):
        """Simulate the self-referential model scenario.

        A factory that raises ImportError if invoked too early succeeds once the
        'module' becomes available — exactly what happens with a self-referential
        pid-relation when the target class is registered after module import.
        """
        module_ready: list[bool] = []  # empty = not yet initialized

        def factory():
            if not module_ready:
                raise ImportError(
                    "cannot import name 'ResearchActivityRecord' from partially "
                    "initialized module 'research_activity'"
                )
            return SimpleNamespace(pid_type="research-activity")

        # Model construction phase: proxy created before module is ready.
        # Without LazyPIDFieldProxy, calling factory() here would raise ImportError.
        proxy = LazyPIDFieldProxy(factory)

        # Module finishes loading (all classes are now available).
        module_ready.append(True)

        # First I/O access — factory is invoked only now, safely.
        assert proxy.pid_type == "research-activity"

    def test_slot_access_does_not_trigger_resolution(self):
        """Accessing _factory via its __slot__ must NOT invoke the factory.

        __slots__ causes _factory to be found via the normal descriptor protocol
        (bypassing __getattr__ entirely), so reading proxy._factory returns the
        stored callable directly without triggering lazy resolution.  This
        confirms that __getattr__ is only invoked for attributes the proxy does
        NOT own itself — i.e. attributes delegated to the resolved object.
        """
        call_log: list[int] = []
        sentinel_factory = lambda: (call_log.append(1), SimpleNamespace())[1]  # noqa: E731
        proxy = LazyPIDFieldProxy(sentinel_factory)

        # Accessing the slot attribute directly must not call the factory.
        stored = object.__getattribute__(proxy, "_factory")
        assert call_log == [], "__slots__ access must not trigger factory resolution"
        assert stored is sentinel_factory, "_factory slot must hold the original callable"


# ---------------------------------------------------------------------------
# AddPIDRelation.apply() lazy-wrapping tests
# ---------------------------------------------------------------------------

class TestAddPIDRelationApplyLaziness:
    """apply() must wrap callable pid_field factories in LazyPIDFieldProxy."""

    def _make_relation(self, pid_field, path=None, **kwargs):
        return AddPIDRelation(
            name="test_rel",
            path=path or ["test_rel"],
            keys=["id"],
            pid_field=pid_field,
            **kwargs,
        )

    def test_apply_wraps_callable_in_lazy_proxy(self):
        """When pid_field is callable, apply() must store a LazyPIDFieldProxy
        in the relations dict rather than calling the factory eagerly."""
        call_log: list[int] = []
        resolved = SimpleNamespace(pid_type="recid")

        def factory():
            call_log.append(1)
            return resolved

        relation = self._make_relation(pid_field=factory)
        builder = _FakeBuilder()
        relation.apply(builder, model=None)

        assert call_log == [], (
            "apply() must NOT invoke the factory; factory was called eagerly"
        )
        stored = builder.get_dictionary("relations")["test_rel"]
        # The stored relation object must carry a LazyPIDFieldProxy as its pid_field
        assert isinstance(stored.pid_field, LazyPIDFieldProxy), (
            f"expected LazyPIDFieldProxy, got {type(stored.pid_field)}"
        )

    def test_apply_does_not_wrap_non_callable(self):
        """When pid_field is already a resolved object (not callable), apply()
        must pass it through unchanged — no unnecessary wrapping."""
        sentinel = SimpleNamespace(pid_type="recid")
        relation = self._make_relation(pid_field=sentinel)
        builder = _FakeBuilder()
        relation.apply(builder, model=None)

        stored = builder.get_dictionary("relations")["test_rel"]
        assert stored.pid_field is sentinel, (
            "Non-callable pid_field must be stored as-is, not wrapped"
        )

    def test_proxy_resolves_correctly_after_apply(self):
        """The LazyPIDFieldProxy stored by apply() must resolve to the correct
        value when an attribute is first accessed after apply() returns."""
        resolved = SimpleNamespace(pid_type="vocab-id")
        relation = self._make_relation(pid_field=lambda: resolved)
        builder = _FakeBuilder()
        relation.apply(builder, model=None)

        stored = builder.get_dictionary("relations")["test_rel"]
        assert stored.pid_field.pid_type == "vocab-id"

    def test_apply_callable_not_called_for_list_relation(self):
        """apply() must also defer the factory for list (array) pid-relations."""
        call_log: list[int] = []

        def factory():
            call_log.append(1)
            return SimpleNamespace(pid_type="recid")

        # path with one ARRAY_PATH_ITEM → PIDListRelation branch
        relation = self._make_relation(
            pid_field=factory,
            path=["items", ARRAY_PATH_ITEM, "id"],
        )
        builder = _FakeBuilder()
        relation.apply(builder, model=None)

        assert call_log == [], (
            "apply() must not call factory eagerly for list relations either"
        )
        stored = builder.get_dictionary("relations")["test_rel"]
        assert isinstance(stored.pid_field, LazyPIDFieldProxy)
