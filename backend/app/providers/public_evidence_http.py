"""Small, transparent public fetcher. No retries or access-control workarounds."""

import hashlib
import ssl
from urllib.parse import urljoin, urlsplit
from urllib.robotparser import RobotFileParser

import httpx

from app.schemas.research_evidence import ResearchState

USER_AGENT = "AutoExpertResearch/0.6.7"


class PublicAccessError(Exception):
    def __init__(self, state, reason, url, http_status=None):
        super().__init__(reason)
        self.state, self.reason, self.url, self.http_status = state, reason, url, http_status


class PublicEvidenceHTTP:
    def __init__(self, transport=None):
        self.client = httpx.Client(
            timeout=15,
            verify=ssl.create_default_context(),
            transport=transport,
            headers={"User-Agent": USER_AGENT},
            follow_redirects=False,
        )
        self.robots = {}
        self.audit = []

    def close(self):
        self.client.close()

    def _request(self, url):
        try:
            with self.client.stream("GET", url) as response:
                data = bytearray()
                for chunk in response.iter_bytes():
                    data.extend(chunk)
                    if len(data) > 4_000_000:
                        raise PublicAccessError(ResearchState.ERROR, "RESPONSE_TOO_LARGE", url)
                r = httpx.Response(
                    response.status_code,
                    headers=response.headers,
                    content=bytes(data),
                    request=response.request,
                )
        except httpx.HTTPError as exc:
            raise PublicAccessError(
                ResearchState.PROVIDER_UNAVAILABLE, type(exc).__name__, url
            ) from exc
        self.audit.append(
            {
                "url": url,
                "http_status": r.status_code,
                "sha256": hashlib.sha256(r.content).hexdigest(),
            }
        )
        if r.status_code >= 400:
            state = {
                401: ResearchState.AUTH_REQUIRED,
                403: ResearchState.PROVIDER_UNAVAILABLE,
                429: ResearchState.RATE_LIMITED,
            }.get(r.status_code, ResearchState.ERROR)
            raise PublicAccessError(state, f"HTTP_{r.status_code}", url, r.status_code)
        if any(
            x in r.text.casefold()
            for x in ("cf-chl-", "verify you are human", "performing security verification")
        ):
            raise PublicAccessError(
                ResearchState.PROVIDER_UNAVAILABLE, "ACCESS_CHALLENGE", url, r.status_code
            )
        return r

    def get(self, url, *, allowed_hosts):
        for _ in range(4):
            parsed = urlsplit(url)
            if parsed.scheme != "https" or parsed.hostname not in allowed_hosts:
                raise PublicAccessError(ResearchState.ERROR, "UNAPPROVED_SOURCE_HOST", url)
            origin = f"https://{parsed.netloc}"
            if origin not in self.robots:
                r = self._request(origin + "/robots.txt")
                if r.is_redirect or "<html" in r.text.casefold():
                    raise PublicAccessError(
                        ResearchState.PROVIDER_UNAVAILABLE, "ROBOTS_UNRESOLVED", url
                    )
                robot = RobotFileParser()
                robot.parse(r.text.splitlines())
                self.robots[origin] = robot
            robot = self.robots[origin]
            # Honour both the app crawler and an explicitly blocked assistant.
            if not all(robot.can_fetch(ua, url) for ua in (USER_AGENT, "ChatGPT-User")):
                raise PublicAccessError(ResearchState.PROVIDER_UNAVAILABLE, "ROBOTS_DISALLOW", url)
            r = self._request(url)
            if not r.is_redirect:
                return r
            url = urljoin(url, r.headers.get("location", ""))
        raise PublicAccessError(ResearchState.ERROR, "REDIRECT_LIMIT", url)
