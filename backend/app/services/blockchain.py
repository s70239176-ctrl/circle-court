import uuid
from decimal import Decimal
from typing import Any

from app.core.config import get_settings


class EscrowChainClient:
    def __init__(self) -> None:
        self.settings = get_settings()

    async def register_escrow(self, *, contract_id: str, buyer: str, seller: str, amount_usdc: Decimal) -> dict[str, Any]:
        if self.settings.web3_simulation_mode or not self.settings.web3_rpc_url:
            return {"mode": "simulation", "chain_escrow_id": f"sim-chain-{contract_id}", "tx_hash": f"0x{uuid.uuid4().hex}"}
        from web3 import Web3

        web3 = Web3(Web3.HTTPProvider(self.settings.web3_rpc_url))
        return {
            "mode": "web3-ready",
            "chain_escrow_id": contract_id,
            "tx_hash": None,
            "connected": web3.is_connected(),
            "contract_address": self.settings.escrow_contract_address,
        }

    async def execute_resolution(self, *, chain_escrow_id: str | None, release_to_seller_pct: Decimal) -> dict[str, Any]:
        if self.settings.web3_simulation_mode or not self.settings.web3_rpc_url:
            return {"mode": "simulation", "tx_hash": f"0x{uuid.uuid4().hex}", "chain_escrow_id": chain_escrow_id, "release_to_seller_pct": str(release_to_seller_pct)}
        return {"mode": "web3-ready", "tx_hash": None, "chain_escrow_id": chain_escrow_id}
