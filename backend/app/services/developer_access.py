from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Request

from app.core.config import get_settings

SIMULATE_USER_PAYWALL_HEADER = "X-AutoExpert-Simulate-Paywall"
_TRUE_VALUES = {"1", "true", "yes", "on"}
_FALSE_VALUES = {"0", "false", "no", "off"}


@dataclass(frozen=True)
class DeveloperAccessContext:
    """Server-authoritative developer access for an already authenticated owner.

    The request header can only opt a developer *into* the ordinary paywall. It can
    never enable developer access when the server-side setting is disabled.
    """

    enabled: bool
    simulate_user_paywall: bool

    @property
    def bypass_paywall(self) -> bool:
        return self.enabled and not self.simulate_user_paywall

    @property
    def diagnostics_visible(self) -> bool:
        return self.enabled


def get_developer_access(request: Request) -> DeveloperAccessContext:
    settings = get_settings()
    if settings.environment == "production" or not settings.developer_mode:
        return DeveloperAccessContext(enabled=False, simulate_user_paywall=False)

    raw = request.headers.get(SIMULATE_USER_PAYWALL_HEADER)
    if raw is None:
        simulate = settings.developer_simulate_user_paywall_default
    elif raw.strip().casefold() in _TRUE_VALUES:
        simulate = True
    elif raw.strip().casefold() in _FALSE_VALUES:
        simulate = False
    else:
        simulate = settings.developer_simulate_user_paywall_default
    return DeveloperAccessContext(enabled=True, simulate_user_paywall=simulate)


DeveloperAccess = Annotated[DeveloperAccessContext, Depends(get_developer_access)]
