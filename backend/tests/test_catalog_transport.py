"""Large evidence-rich responses retain all fields under negotiated compression."""

from app.main import create_app
from fastapi.testclient import TestClient


def test_large_catalog_response_compression_preserves_unicode_and_evidence():
    app = create_app()
    payload = {
        "cards": [
            {"id": i, "az": "Mühərrik", "ru": "Двигатель", "evidence": "source-page-12 " * 800}
            for i in range(120)
        ]
    }

    @app.get("/test-catalog-transport")
    def response():
        return payload

    with TestClient(app) as client:
        raw = client.get("/test-catalog-transport", headers={"Accept-Encoding": "identity"})
        compressed = client.get("/test-catalog-transport", headers={"Accept-Encoding": "gzip"})
    assert len(raw.content) > 1024 * 1024
    assert "content-encoding" not in raw.headers
    assert compressed.headers["content-encoding"] == "gzip"
    assert "Accept-Encoding" in compressed.headers["vary"]
    assert int(compressed.headers["content-length"]) < len(raw.content) // 10
    assert raw.json() == compressed.json() == payload
