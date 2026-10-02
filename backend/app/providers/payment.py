from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

from app.providers.base import PaymentResult


class MockPaymentProvider:
    name = "mock"

    def __init__(self, *, should_succeed: bool = True):
        self.should_succeed = should_succeed

    def charge(
        self, *, report_id: str, user_id: str, amount: Decimal, currency: str
    ) -> PaymentResult:
        return PaymentResult(
            succeeded=self.should_succeed,
            external_id=f"mock_{uuid4()}" if self.should_succeed else None,
            provider_payload={
                "mode": "development",
                "report_id": report_id,
                "amount": str(amount),
                "currency": currency,
                "result": "success" if self.should_succeed else "failure",
            },
        )
