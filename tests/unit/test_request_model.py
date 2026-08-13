from __future__ import annotations

from decimal import Decimal

import pytest
from pydantic import ValidationError

from ncins_premium.models import CalculatePremiumRequest, InsuranceObject, is_iso_date
from ncins_premium.payloads import example_payload, payload_with


@pytest.mark.unit
class TestCalculatePremiumRequestModel:
    def test_example_payload_is_valid(self):
        model = CalculatePremiumRequest.model_validate(example_payload())
        assert model.program_id == 3
        assert model.duration == 12
        assert model.insurance_sum == Decimal("500000.00")
        assert len(model.insurance_objects) == 1
        assert model.insurance_objects[0].employee_fio == "Сидоров Иван Сергеевич"

    def test_to_api_dict_uses_aliases(self):
        model = CalculatePremiumRequest.model_validate(example_payload())
        raw = model.to_api_dict()
        assert set(raw) == {"programId", "duration", "insuranceSum", "insuranceObjects"}
        assert raw["insuranceObjects"][0]["employeeBirthDate"] == "1995-05-20"

    @pytest.mark.parametrize(
        "field,value",
        [
            ("programId", 0),
            ("programId", -1),
            ("programId", "abc"),
            ("duration", 0),
            ("duration", -12),
            ("insuranceSum", 0),
            ("insuranceSum", -1),
            ("insuranceSum", "not-a-number"),
        ],
    )
    def test_invalid_scalar_fields_rejected(self, field, value):
        payload = payload_with(**{field: value})
        with pytest.raises(ValidationError):
            CalculatePremiumRequest.model_validate(payload)

    def test_empty_insurance_objects_rejected(self):
        payload = payload_with(insuranceObjects=[])
        with pytest.raises(ValidationError):
            CalculatePremiumRequest.model_validate(payload)

    def test_missing_required_top_level_field(self):
        payload = example_payload()
        del payload["programId"]
        with pytest.raises(ValidationError):
            CalculatePremiumRequest.model_validate(payload)

    @pytest.mark.parametrize(
        "field",
        ["employeeFIO", "employeeBirthDate", "employeeEmail", "employeePhoneNumber"],
    )
    def test_missing_employee_field_rejected(self, field):
        payload = example_payload()
        del payload["insuranceObjects"][0][field]
        with pytest.raises(ValidationError):
            CalculatePremiumRequest.model_validate(payload)

    @pytest.mark.parametrize(
        "email",
        ["", "not-email", "a@", "@b.ru", "sidorov example.com"],
    )
    def test_invalid_email_rejected(self, email):
        payload = example_payload()
        payload["insuranceObjects"][0]["employeeEmail"] = email
        with pytest.raises(ValidationError):
            CalculatePremiumRequest.model_validate(payload)

    @pytest.mark.parametrize(
        "phone",
        ["", "123", "+", "abc", "12345"],
    )
    def test_invalid_phone_rejected(self, phone):
        payload = example_payload()
        payload["insuranceObjects"][0]["employeePhoneNumber"] = phone
        with pytest.raises(ValidationError):
            CalculatePremiumRequest.model_validate(payload)

    def test_multiple_insurance_objects_accepted(self):
        payload = example_payload()
        payload["insuranceObjects"].append(
            {
                "employeeFIO": "Иванова Анна Петровна",
                "employeeBirthDate": "1988-11-03",
                "employeeEmail": "ivanova@example.com",
                "employeePhoneNumber": "+79992223344",
            }
        )
        model = CalculatePremiumRequest.model_validate(payload)
        assert len(model.insurance_objects) == 2

    def test_extra_fields_forbidden(self):
        payload = payload_with(unexpectedField=True)
        with pytest.raises(ValidationError):
            CalculatePremiumRequest.model_validate(payload)


@pytest.mark.unit
class TestHelpers:
    @pytest.mark.parametrize(
        "value,expected",
        [
            ("1995-05-20", True),
            ("2026-08-11", True),
            ("20.05.1995", False),
            ("1995/05/20", False),
            ("1995-13-01", False),
            ("", False),
        ],
    )
    def test_is_iso_date(self, value, expected):
        assert is_iso_date(value) is expected

    def test_insurance_object_alias_roundtrip(self):
        obj = InsuranceObject.model_validate(
            {
                "employeeFIO": "Сидоров Иван Сергеевич",
                "employeeBirthDate": "1995-05-20",
                "employeeEmail": "sidorov@example.com",
                "employeePhoneNumber": "+79991112233",
            }
        )
        dumped = obj.model_dump(by_alias=True, mode="json")
        assert dumped["employeeFIO"] == "Сидоров Иван Сергеевич"
