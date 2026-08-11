from __future__ import annotations

import pytest

from ncins_premium.payloads import example_payload, payload_with


pytestmark = [pytest.mark.integration, pytest.mark.usefixtures("skip_if_gateway_unavailable")]

CLIENT_ERROR = {400, 422}


def _assert_client_error(response):
    assert response.status_code in CLIENT_ERROR, (
        f"Expected client error {CLIENT_ERROR}, got {response.status_code}: {response.text}"
    )


@pytest.mark.parametrize(
    "field",
    ["programId", "duration", "insuranceSum", "insuranceObjects"],
)
def test_missing_required_field_returns_client_error(client, field):
    payload = example_payload()
    del payload[field]
    response = client.calculate(payload)
    _assert_client_error(response)


@pytest.mark.parametrize(
    "field,value",
    [
        ("programId", None),
        ("programId", 0),
        ("programId", -1),
        ("programId", "3"),
        ("programId", 3.5),
        ("duration", None),
        ("duration", 0),
        ("duration", -1),
        ("duration", "12"),
        ("duration", 12.5),
        ("insuranceSum", None),
        ("insuranceSum", 0),
        ("insuranceSum", -100),
        ("insuranceSum", "500000"),
        ("insuranceSum", True),
    ],
)
def test_invalid_scalar_values_return_client_error(client, field, value):
    response = client.calculate(payload_with(**{field: value}))
    _assert_client_error(response)


def test_empty_insurance_objects_returns_client_error(client):
    response = client.calculate(payload_with(insuranceObjects=[]))
    _assert_client_error(response)


def test_insurance_objects_not_array_returns_client_error(client):
    response = client.calculate(payload_with(insuranceObjects={"employeeFIO": "x"}))
    _assert_client_error(response)


@pytest.mark.parametrize(
    "field",
    ["employeeFIO", "employeeBirthDate", "employeeEmail", "employeePhoneNumber"],
)
def test_missing_employee_field_returns_client_error(client, field):
    payload = example_payload()
    del payload["insuranceObjects"][0][field]
    response = client.calculate(payload)
    _assert_client_error(response)


@pytest.mark.parametrize(
    "birth_date",
    ["", "20.05.1995", "1995/05/20", "1995-13-40", "not-a-date", 19950520],
)
def test_invalid_birth_date_returns_client_error(client, birth_date):
    payload = example_payload()
    payload["insuranceObjects"][0]["employeeBirthDate"] = birth_date
    response = client.calculate(payload)
    _assert_client_error(response)


@pytest.mark.parametrize(
    "email",
    ["", "plainaddress", "a@", "@b.ru", "sidorov example.com", 123],
)
def test_invalid_email_returns_client_error(client, email):
    payload = example_payload()
    payload["insuranceObjects"][0]["employeeEmail"] = email
    response = client.calculate(payload)
    _assert_client_error(response)


@pytest.mark.parametrize(
    "phone",
    ["", "123", "phone", "+", None],
)
def test_invalid_phone_returns_client_error(client, phone):
    payload = example_payload()
    payload["insuranceObjects"][0]["employeePhoneNumber"] = phone
    response = client.calculate(payload)
    _assert_client_error(response)


@pytest.mark.parametrize(
    "fio",
    ["", " ", None, 12345],
)
def test_invalid_fio_returns_client_error(client, fio):
    payload = example_payload()
    payload["insuranceObjects"][0]["employeeFIO"] = fio
    response = client.calculate(payload)
    _assert_client_error(response)


def test_unknown_program_id_returns_client_or_business_error(client):
    response = client.calculate(payload_with(programId=999999999))
    assert response.status_code in {400, 404, 422}, response.text


def test_future_birth_date_returns_client_error(client):
    payload = example_payload()
    payload["insuranceObjects"][0]["employeeBirthDate"] = "2999-01-01"
    response = client.calculate(payload)
    _assert_client_error(response)


def test_empty_body_returns_client_error(client, settings):
    response = client.session.post(
        settings.calculate_url,
        data="",
        headers=settings.default_headers(),
        timeout=settings.timeout,
    )
    assert response.status_code in CLIENT_ERROR | {415}, response.text


def test_malformed_json_returns_client_error(client, settings):
    headers = settings.default_headers()
    response = client.session.post(
        settings.calculate_url,
        data="{not-json",
        headers=headers,
        timeout=settings.timeout,
    )
    assert response.status_code in CLIENT_ERROR | {415}, response.text
