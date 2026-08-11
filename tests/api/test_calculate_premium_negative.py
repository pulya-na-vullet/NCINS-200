from __future__ import annotations

import pytest

from ncins_premium.payloads import example_payload, payload_with


pytestmark = [pytest.mark.integration, pytest.mark.usefixtures("skip_if_gateway_unavailable")]


def test_very_large_insurance_sum_handled(client):
    """Сверхбольшая сумма не должна ронять сервис 5xx."""
    response = client.calculate(payload_with(insuranceSum=10**18))
    assert response.status_code < 500, response.text


def test_very_large_duration_handled(client):
    response = client.calculate(payload_with(duration=10**9))
    assert response.status_code < 500, response.text


def test_many_insurance_objects_handled(client):
    payload = example_payload()
    base = payload["insuranceObjects"][0]
    payload["insuranceObjects"] = [
        {
            **base,
            "employeeFIO": f"Сотрудник {i} Тестов",
            "employeeEmail": f"user{i}@example.com",
            "employeePhoneNumber": f"+7999{i:07d}",
        }
        for i in range(50)
    ]
    response = client.calculate(payload)
    assert response.status_code < 500, response.text


def test_sql_injection_in_fio_does_not_break_service(client):
    payload = example_payload()
    payload["insuranceObjects"][0]["employeeFIO"] = "Robert'); DROP TABLE tariffs;--"
    response = client.calculate(payload)
    assert response.status_code < 500, response.text


def test_xss_payload_in_email_local_part_rejected_or_safe(client):
    payload = example_payload()
    payload["insuranceObjects"][0]["employeeEmail"] = "<script>alert(1)</script>@example.com"
    response = client.calculate(payload)
    assert response.status_code < 500, response.text


def test_unicode_fio_accepted_or_validated(client):
    payload = example_payload()
    payload["insuranceObjects"][0]["employeeFIO"] = "O'Connor José María"
    response = client.calculate(payload)
    assert response.status_code < 500, response.text


def test_duplicate_employee_objects_do_not_crash(client):
    payload = example_payload()
    payload["insuranceObjects"] = [
        payload["insuranceObjects"][0],
        payload["insuranceObjects"][0],
    ]
    response = client.calculate(payload)
    assert response.status_code < 500, response.text


def test_unknown_top_level_field_ignored_or_rejected(client):
    payload = payload_with(hackField="boom")
    response = client.calculate(payload)
    assert response.status_code in {200, 400, 422}, response.text
