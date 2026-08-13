"""Валидация тела запроса POST /v1/sign/create-operation."""

from __future__ import annotations

import pytest

from ncins_sign.payloads import example_payload, payload_with

pytestmark = [pytest.mark.integration, pytest.mark.usefixtures("skip_if_gateway_unavailable")]

CLIENT_ERROR = {400, 422}


def _assert_client_error(response):
    assert response.status_code in CLIENT_ERROR, (
        f"Expected {CLIENT_ERROR}, got {response.status_code}: {response.text}"
    )


@pytest.mark.parametrize(
    "field,case_no",
    [
        ("userId", "13"),
        ("clientId", "14"),
        ("documentId", "15"),
    ],
)
def test_missing_required_body_field(client, field, case_no):
    """№13–15: отсутствие обязательного поля тела → 400/422."""
    payload = example_payload()
    del payload[field]
    _assert_client_error(client.create_operation(payload))


@pytest.mark.parametrize(
    "field,value,case_no",
    [
        ("userId", "", "16"),
        ("userId", None, "17"),
        ("clientId", "", "18"),
        ("clientId", None, "19"),
        ("documentId", "", "20"),
        ("documentId", None, "21"),
    ],
)
def test_empty_or_null_required_field(client, field, value, case_no):
    """№16–21: пустые/null обязательные поля → 400/422."""
    _assert_client_error(client.create_operation(payload_with(**{field: value})))


def test_22_invalid_document_id_not_uuid(client):
    """№22: documentId не UUID → 400/422."""
    _assert_client_error(client.create_operation(payload_with(documentId="not-a-uuid")))


def test_23_unknown_document_id(client):
    """№23: несуществующий documentId → 400/404/422."""
    response = client.create_operation(
        payload_with(documentId="00000000-0000-4000-8000-000000000000")
    )
    assert response.status_code in {400, 404, 422}, response.text


def test_24_empty_body_rejected(client, settings):
    """№24: пустое тело {} → 400/422."""
    response = client.create_operation({})
    _assert_client_error(response)


def test_25_extra_unknown_field(client):
    """№25: лишнее поле в теле — либо 400/422, либо игнор (200/201)."""
    payload = example_payload()
    payload["unexpectedField"] = "x"
    response = client.create_operation(payload)
    assert response.status_code in {200, 201, 400, 422}, response.text
