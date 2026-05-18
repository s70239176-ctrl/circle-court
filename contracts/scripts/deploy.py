import json
import os
from pathlib import Path

from solcx import compile_standard, install_solc
from web3 import Web3
from eth_account import Account


def main() -> None:
    rpc_url = os.environ["WEB3_RPC_URL"]
    private_key = os.environ["DEPLOYER_PRIVATE_KEY"]
    chain_id = int(os.getenv("CHAIN_ID", "11155111"))
    source = Path("contracts/CircleCourtEscrow.sol").read_text(encoding="utf-8")
    install_solc("0.8.24")
    compiled = compile_standard(
        {
            "language": "Solidity",
            "sources": {"CircleCourtEscrow.sol": {"content": source}},
            "settings": {"outputSelection": {"*": {"*": ["abi", "evm.bytecode"]}}},
        },
        solc_version="0.8.24",
    )
    artifact = compiled["contracts"]["CircleCourtEscrow.sol"]["CircleCourtEscrow"]
    web3 = Web3(Web3.HTTPProvider(rpc_url))
    account = Account.from_key(private_key)
    contract = web3.eth.contract(abi=artifact["abi"], bytecode=artifact["evm"]["bytecode"]["object"])
    tx = contract.constructor().build_transaction(
        {
            "from": account.address,
            "nonce": web3.eth.get_transaction_count(account.address),
            "gas": 2_200_000,
            "gasPrice": web3.eth.gas_price,
            "chainId": chain_id,
        }
    )
    signed = account.sign_transaction(tx)
    tx_hash = web3.eth.send_raw_transaction(signed.rawTransaction)
    receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
    output = {"address": receipt.contractAddress, "txHash": tx_hash.hex(), "abi": artifact["abi"]}
    Path("contracts/deployment.json").write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
