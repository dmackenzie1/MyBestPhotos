from photo_curator.pipeline_v1.llm_stage import _chat_completions_endpoint, _extract_content_text


def test_chat_completions_endpoint_accepts_base_with_v1() -> None:
    assert (
        _chat_completions_endpoint("http://127.0.0.1:1234/v1")
        == "http://127.0.0.1:1234/v1/chat/completions"
    )


def test_chat_completions_endpoint_adds_v1_when_missing() -> None:
    assert (
        _chat_completions_endpoint("http://127.0.0.1:1234")
        == "http://127.0.0.1:1234/v1/chat/completions"
    )


def test_extract_content_text_handles_openai_list_format() -> None:
    content = [
        {"type": "text", "text": '{"description":"hello"}'},
        {"type": "image", "image_url": {"url": "data:image/jpeg;base64,abc"}},
    ]
    assert _extract_content_text(content) == '{"description":"hello"}'
