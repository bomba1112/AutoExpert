import ssl
from unittest.mock import patch

import httpx
from app.providers.official_nhtsa import OfficialHTTPClient


def test_default_provider_client_uses_system_roots_with_tls_verification():
    with patch("app.providers.official_nhtsa.httpx.Client") as factory:
        OfficialHTTPClient()
    context = factory.call_args.kwargs["verify"]
    assert isinstance(context, ssl.SSLContext)
    assert context.verify_mode == ssl.CERT_REQUIRED
    assert context.check_hostname is True
    assert context.cert_store_stats()["x509_ca"] > 0


def test_injected_provider_transport_still_works():
    transport = httpx.MockTransport(lambda request: httpx.Response(200, json={"Count": 0}))
    with httpx.Client(transport=transport) as client:
        provider = OfficialHTTPClient(client=client)
        assert provider.get_json("https://provider.example/test") == ({"Count": 0}, 1)
