"""9–23 — валидация тела запроса метода calculate."""

from __future__ import annotations

import pytest

from ncins_premium.payloads import example_payload, payload_with

pytestmark = [pytest.mark.integration, pytest.mark.usefixtures("skip_if_gateway_unavailable")]

CLIENT_ERROR = {400, 422}


def _assert_client_error(response):
    assert response.status_code in CLIENT_ERROR, (
        f"Expected {CLIENT_ERROR}, got {response.status_code}: {response.text}"
    )


@pytest.mark.parametrize(
    "field,case_no",
    [
        ("programId", "09"),
        ("duration", "10"),
        ("insuranceSum", "11"),
        ("insuranceObjects", "12"),
    ],
)
def test_missing_required_top_level_field(client, field, case_no):
    """№9–12: отсутствие обязательного поля тела → 400/422."""
    payload = example_payload()
    del payload[field]
    _assert_client_error(client.calculate(payload))


def test_13_empty_insurance_objects(client):
    """№13: пустой массив insuranceObjects → 400/422."""
    _assert_client_error(client.calculate(payload_with(insuranceObjects=[])))


@pytest.mark.parametrize(
    "field,case_no",
    [
        ("employeeFIO", "14"),
        ("employeeBirthDate", "15"),
        ("employeeEmail", "16"),
        ("employeePhoneNumber", "17"),
    ],
)
def test_missing_employee_field(client, field, case_no):
    """№14–17: отсутствие поля сотрудника → 400/422."""
    payload = example_payload()
    del payload["insuranceObjects"][0][field]
    _assert_client_error(client.calculate(payload))


def test_18_invalid_email(client):
    """№18: невалидный email → 400/422."""
    payload = example_payload()
    payload["insuranceObjects"][0]["employeeEmail"] = "not-an-email"
    _assert_client_error(client.calculate(payload))


def test_19_invalid_birth_date(client):
    """№19: дата не в формате YYYY-MM-DD → 400/422."""
    payload = example_payload()
    payload["insuranceObjects"][0]["employeeBirthDate"] = "20.05.1995"
    _assert_client_error(client.calculate(payload))


def test_20_invalid_phone(client):
    """№20: невалидный телефон → 400/422."""
    payload = example_payload()
    payload["insuranceObjects"][0]["employeePhoneNumber"] = "123"
    _assert_client_error(client.calculate(payload))


@pytest.mark.parametrize("value", [0, -100, "abc"])
def test_21_invalid_insurance_sum(client, value):
    """№21: невалидная страховая сумма → 400/422."""
    _assert_client_error(client.calculate(payload_with(insuranceSum=value)))


@pytest.mark.parametrize("value", [0, -1])
def test_22_invalid_duration(client, value):
    """№22: невалидный срок → 400/422."""
    _assert_client_error(client.calculate(payload_with(duration=value)))


def test_23_unknown_program_id(client):
    """№23: неизвестный programId → 400/404/422."""
    response = client.calculate(payload_with(programId=999999999))
    assert response.status_code in {400, 404, 422}, response.text
