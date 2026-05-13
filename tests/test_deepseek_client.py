import httpx
import pytest

from app.core.config import Settings
from app.services.deepseek_client import DeepSeekClient, DeepSeekError


class FakeHTTPClient:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def post(self, url, *, headers, json, timeout):
        self.calls.append({"url": url, "headers": headers, "json": json, "timeout": timeout})
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


def response_with(content: str) -> httpx.Response:
    return httpx.Response(
        200,
        json={"choices": [{"message": {"content": content}}]},
        request=httpx.Request("POST", "https://api.deepseek.com/chat/completions"),
    )


def settings(**overrides):
    values = {
        "deepseek_api_key": "test-key",
        "deepseek_base_url": "https://api.deepseek.com",
        "deepseek_model": "deepseek-test",
        "deepseek_max_retries": 1,
    }
    values.update(overrides)
    return Settings(**values)


def test_generate_question_uses_configured_deepseek_endpoint():
    fake = FakeHTTPClient(
        [
            response_with(
                '{"question_id":"q1","text":"Please provide shipper phone.","requested_fields":[{"field_name":"shipper_phone"}],"conflicts":[],"round_number":1}'
            )
        ]
    )
    client = DeepSeekClient(settings=settings(), http_client=fake)

    question = client.generate_question({"missing_fields": ["shipper_phone"]})

    assert question.question_id == "q1"
    assert fake.calls[0]["url"] == "https://api.deepseek.com/chat/completions"
    assert fake.calls[0]["headers"]["Authorization"] == "Bearer test-key"
    assert fake.calls[0]["json"]["model"] == "deepseek-test"


def test_generate_question_accepts_requested_field_names_from_model():
    fake = FakeHTTPClient(
        [
            response_with(
                '{"question_id":"q1","text":"Please provide missing details.","requested_fields":["shipper_phone","consignee_phone"],"conflicts":[],"round_number":1}'
            )
        ]
    )
    client = DeepSeekClient(settings=settings(), http_client=fake)

    question = client.generate_question({"missing_fields": ["shipper_phone", "consignee_phone"]})

    assert [field.field_name for field in question.requested_fields] == [
        "shipper_phone",
        "consignee_phone",
    ]


def test_generate_question_validation_failure_is_recoverable_error():
    fake = FakeHTTPClient([response_with('{"question_id":"q1","text":123,"requested_fields":[]}')])
    client = DeepSeekClient(settings=settings(deepseek_max_retries=0), http_client=fake)

    with pytest.raises(DeepSeekError, match="question schema"):
        client.generate_question({})


def test_missing_api_key_is_recoverable_error():
    client = DeepSeekClient(settings=settings(deepseek_api_key=None), http_client=FakeHTTPClient([]))

    with pytest.raises(DeepSeekError, match="API_KEY"):
        client.generate_question({})


def test_invalid_json_retries_once_then_succeeds():
    fake = FakeHTTPClient(
        [
            response_with("not-json"),
            response_with('{"fields":{"shipper_phone":"13800000001"},"resolved_conflicts":[],"confidence":0.9}'),
        ]
    )
    client = DeepSeekClient(settings=settings(), http_client=fake)

    parsed = client.parse_answer({}, "phone is 13800000001")

    assert parsed.fields["shipper_phone"] == "13800000001"
    assert len(fake.calls) == 2


def test_final_invalid_json_failure_is_recoverable_error():
    fake = FakeHTTPClient([response_with("bad"), response_with("still bad")])
    client = DeepSeekClient(settings=settings(), http_client=fake)

    with pytest.raises(DeepSeekError):
        client.parse_answer({}, "anything")
