#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see https://github.com/oarepo/oarepo-model).
#
# oarepo-model is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
from __future__ import annotations

from io import BytesIO
from typing import Any, ClassVar

import pytest
from invenio_app.factory import create_api as _create_api


@pytest.fixture(scope="module")
def create_app(instance_path, entry_points):
    """Application factory fixture."""
    return _create_api


@pytest.fixture(scope="module")
def test_service(app):
    """Service instance."""
    return app.extensions["test"].records_service


@pytest.fixture(scope="module")
def facet_service(app):
    """Service instance."""
    return app.extensions["facet_test"].records_service


@pytest.fixture(scope="module")
def test_draft_service(app):
    """Service instance."""
    return app.extensions["draft_test"].records_service


@pytest.fixture(scope="module")
def draft_service_with_files(app):
    """Service instance."""
    return app.extensions["draft_with_files"].records_service


@pytest.fixture(scope="module")
def draft_file_service(app):
    """Service instance."""
    return app.extensions["draft_with_files"].draft_files_service


@pytest.fixture(scope="module")
def file_service(app):
    """Service instance."""
    return app.extensions["test"].files_service


@pytest.fixture(scope="module")
def test_rdm_service(app):
    """Service instance."""
    return app.extensions["rdm_test"].records_service


@pytest.fixture(scope="module")
def test_rdm_draft_files_service(app):
    """Service instance."""
    return app.extensions["rdm_test"].draft_files_service


@pytest.fixture(scope="module")
def test_rdm_draft_media_files_service(app):
    """Service instance."""
    return app.extensions["rdm_test"].draft_media_files_service


@pytest.fixture(scope="module")
def test_datacite_service(app):
    """Service instance."""
    return app.extensions["datacite_export_test"].records_service


@pytest.fixture(scope="module")
def synthetic_metadata_service(app):
    """Service instance."""
    return app.extensions["synthetic_metadata_test"].records_service


@pytest.fixture
def input_data():
    """Input data (as coming from the view layer)."""
    return {
        "metadata": {"title": "Test"},
        "files": {
            "enabled": True,
        },
    }


@pytest.fixture
def input_data_more_complex():
    """Input data (as coming from the view layer)."""
    return {
        "metadata": {"title": "Test", "some_bool_val": True, "height": 123},
        "files": {
            "enabled": True,
        },
    }


@pytest.fixture
def input_facets_data():
    """Input data with files disabled."""
    return {"files": {"enabled": False}, "metadata": {"b": "jej"}}


@pytest.fixture
def input_data_with_files_disabled(input_data):
    """Input data with files disabled."""
    data = input_data.copy()
    data["files"]["enabled"] = False
    return data


@pytest.fixture
def csv_row_of_input_data_more_complex() -> bytes:
    csv_text = """title,some_bool_val,height
Test,True,123
"""
    return csv_text.encode("utf-8")


class DefaultHeaders:
    """Default headers for requests."""

    json: ClassVar[dict[str, str]] = {
        "content-type": "application/json",
        "accept": "application/json",
    }
    ui: ClassVar[dict[str, str]] = {
        "accept": "application/vnd.inveniordm.v1+json",
    }
    csv: ClassVar[dict[str, str]] = {
        "content-type": "text/csv",
    }


@pytest.fixture(scope="module")
def headers():
    """Return default headers for making requests."""
    return DefaultHeaders


@pytest.fixture
def add_file_to_draft():
    """Add a file to the record."""

    def _add_file_to_draft(draft_file_service, draft_id, file_id, identity) -> dict[str, Any]:
        result = draft_file_service.init_files(identity, draft_id, data=[{"key": file_id}])
        file_md = next(iter(result.entries))
        assert file_md["key"] == "test.txt"
        assert file_md["status"] == "pending"

        draft_file_service.set_file_content(
            identity,
            draft_id,
            file_id,
            BytesIO(b"test file content"),
        )
        result = draft_file_service.commit_file(identity, draft_id, file_id)
        file_md = result.data
        assert file_md["status"] == "completed"
        return result

    return _add_file_to_draft
