import json
import os
from dataclasses import dataclass
from typing import Literal

@dataclass
class Order:
    salt: str
    maker: str
    signer: str
    taker: str
    tokenId: str
    makerAmount: str
    takerAmount: str
    expiration: str
    nonce: str
    feeRateBps: str
    side: str
    signatureType: str
    signature: str

@dataclass
class JSON_schema:
    takerOrder: Order
    makerOrders: list[Order]
    takerFillAmount: str
    takerReceiveAmount: str
    makerFillAmounts: list[str]
    takerFeeAmount: str
    makerFeeAmounts: list[str]

@dataclass
class Transaction:
    log_index: int
    position_id: str
    shares: float
    usdc_amount: float
    action: Literal["BUY", "SELL"]

def get_json_logs(tx_hash):
    file_path = f"./data/json_logs/logs-{tx_hash}.json"
    if not os.path.exists(file_path):
        raise ValueError(f"file does not exist: {file_path}")

    with open(file_path, "r") as f:
        return json.load(f)

def parse_json(json_data, wallet):
    PADDING = 1_000_000

    json_data = JSON_schema(**json_data)

    transactions: list[Transaction] = []
    for i, obj in enumerate(json_data.makerOrders):
        order = Order(**obj) # type: ignore
        if order.maker.lower() != wallet:
            continue
        position_id = hex(int(order.tokenId))
        shares = float(order.makerAmount) / PADDING
        usdc_amount = float(order.takerAmount) / PADDING
        action = "BUY" if order.side == "0" else "SELL"
        transactions.append(Transaction(i, position_id, shares, usdc_amount, action))
    
    # adjust filled shares
    for transaction in transactions:
        filled_shares = float(json_data.makerFillAmounts[transaction.log_index]) / PADDING
        if filled_shares != transaction.shares:
            avg_price = transaction.usdc_amount / transaction.shares
            transaction.shares = filled_shares
            transaction.usdc_amount = avg_price * transaction.shares
    return transactions

def load_tests():
    from json import load
    file_path = "./data/test_cases.json"
    with open(file_path, "r") as f:
        json_data = load(f)
    return json_data


def main():
    from log_parser import tx_hashes
    from calldata_parser import get_calldata, parse_match_orders
    wallet = "0x63ce342161250d705dc0b16df89036c8e5f9ba9a"
    for hash in tx_hashes:
        json_logs = parse_match_orders(get_calldata(hash))
        print(parse_json(json_logs, wallet))

if __name__ == "__main__":
    main()

