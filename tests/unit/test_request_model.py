from __future__ import annotations

import pytest
from pydantic import ValidationError

from ncins_sign.models import CreateOperationRequest, CreateOperationResponse
from ncins_sign.payloads import example_payload, payload_with


@pytest.mark.unit
class TestCreateOperationRequestModel:
    def test_example_payload_is_valid(self):
        model = CreateOperationRequest.model_validate(example_payload())
        assert model.user_id == "XAGA56"
        assert model.client_id == "UAY4DP"
        assert model.document_id == "3fa85f64-5717-4562-b3fc-2c963f66afa6"

    def test_to_api_dict_uses_aliases(self):
        model = CreateOperationRequest.model_validate(example_payload())
        raw = model.to_api_dict()
        assert set(raw) == {"userId", "clientId", "documentId"}

    @pytest.mark.parametrize("field", ["userId", "clientId", "documentId"])
    def test_missing_required_field_rejected(self, field):
        payload = example_payload()
        del payload[field]
        with pytest.raises(ValidationError):
            CreateOperationRequest.model_validate(payload)

    @pytest.mark.parametrize("field", ["userId", "clientId", "documentId"])
    def test_empty_string_rejected(self, field):
        with pytest.raises(ValidationError):
            CreateOperationRequest.model_validate(payload_with(**{field: ""}))

    def test_invalid_document_id_rejected(self):
        with pytest.raises(ValidationError):
            CreateOperationRequest.model_validate(payload_with(documentId="bad-id"))

    def test_extra_fields_forbidden(self):
        payload = payload_with(unexpectedField=True)
        with pytest.raises(ValidationError):
            CreateOperationRequest.model_validate(payload)


@pytest.mark.unit
@pytest.mark.parametrize(
    "payload,expected",
    [
        ({"operationId": "op-1"}, "op-1"),
        ({"id": "abc"}, "abc"),
        ({"data": {"signOperationId": "s-9"}}, "s-9"),
        ({"result": {"uuid": "u-1"}}, "u-1"),
        ({"operation": {"operation_id": "nested"}}, "nested"),
    ],
)
def test_extract_operation_id_supports_common_shapes(payload, expected):
    assert CreateOperationResponse.extract_operation_id(payload) == expected


@pytest.mark.unit
def test_extract_operation_id_raises_when_absent():
    with pytest.raises(AssertionError):
        CreateOperationResponse.extract_operation_id({"status": "ok"})
