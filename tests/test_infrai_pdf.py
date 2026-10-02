import httpx

from contract_signer.infrai_pdf import InfraiPdfClient


def test_generate_request_uses_exact_pdf_fields_and_idempotency_header() -> None:
    captured: dict[str, object] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["method"] = request.method
        captured["path"] = request.url.path
        captured["headers"] = request.headers
        captured["body"] = request.content
        return httpx.Response(200, json={"ok": True, "data": {"id": "signed-7"}, "error": None, "metadata": {}})

    client = InfraiPdfClient("test-key", transport=httpx.MockTransport(handler))
    result = client.generate_contract(
        markdown="# Creator license",
        idempotency_key="contract-7",
    )
    client.close()

    assert result == {"id": "signed-7"}
    assert captured["method"] == "POST"
    assert captured["path"] == "/v1/pdf/generate"
    assert captured["headers"]["idempotency-key"] == "contract-7"  # type: ignore[index]
    assert set(httpx.Response(200, content=captured["body"]).json()) == {
        "markdown", "page_size", "orientation", "store"
    }
