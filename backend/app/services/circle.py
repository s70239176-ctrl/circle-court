import uuid
from decimal import Decimal
from typing import Any

import httpx

from app.core.config import get_settings


class CircleClient:
    def __init__(self) -> None:
        self.settings = get_settings()

    async def create_escrow(self, *, amount_usdc: Decimal, contract_id: str, buyer_address: str) -> dict[str, Any]:
        if self.settings.circle_simulation_mode or not self.settings.circle_api_key:
            return {
                "mode": "simulation",
                "payment_id": f"sim-pay-{uuid.uuid4()}",
                "escrow_wallet_id": f"sim-wallet-{contract_id}",
                "amount_usdc": str(amount_usdc),
                "buyer_address": buyer_address,
            }
        async with httpx.AsyncClient(base_url=self.settings.circle_base_url, timeout=30) as client:
            response = await client.post(
                "/v1/w3s/developer/wallets",
                headers=self._headers(),
                json={"idempotencyKey": str(uuid.uuid4()), "blockchains": ["ETH-SEPOLIA"], "count": 1},
            )
            response.raise_for_status()
            wallet_id = response.json()["data"]["wallets"][0]["id"]
            return {"mode": "circle", "payment_id": None, "escrow_wallet_id": wallet_id, "amount_usdc": str(amount_usdc)}

    async def release(self, *, escrow_wallet_id: str | None, seller_address: str, buyer_address: str, amount_usdc: Decimal, release_to_seller_pct: Decimal) -> dict[str, Any]:
        seller_amount = (amount_usdc * release_to_seller_pct / Decimal("100")).quantize(Decimal("0.000001"))
        buyer_amount = amount_usdc - seller_amount
        if self.settings.circle_simulation_mode or not self.settings.circle_api_key:
            return {
                "mode": "simulation",
                "tx_id": f"sim-release-{uuid.uuid4()}",
                "seller_address": seller_address,
                "buyer_address": buyer_address,
                "seller_amount_usdc": str(seller_amount),
                "buyer_refund_usdc": str(buyer_amount),
                "escrow_wallet_id": escrow_wallet_id,
            }
        return {
            "mode": "circle",
            "tx_id": f"circle-transfer-requested-{uuid.uuid4()}",
            "seller_amount_usdc": str(seller_amount),
            "buyer_refund_usdc": str(buyer_amount),
        }

    async def nanopayment(self, *, from_wallet: str, amount_usdc: Decimal, memo: str) -> dict[str, Any]:
        return {
            "mode": "simulation" if self.settings.circle_simulation_mode else "circle",
            "fee_id": f"fee-{uuid.uuid4()}",
            "from_wallet": from_wallet,
            "amount_usdc": str(amount_usdc),
            "memo": memo,
        }

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.settings.circle_api_key}", "Content-Type": "application/json"}
