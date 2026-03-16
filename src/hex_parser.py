"""
Polymarket CTF Exchange - matchOrders Calldata Parser
Parses raw calldata hex into the Polymarket API JSON structure.
"""
import json
import os
from dataclasses import dataclass
from typing import Literal

def _words(hex_str: str) -> list[str]:
    raw = hex_str.removeprefix("0x")[8:]  # strip 4-byte selector
    return [raw[i:i+64] for i in range(0, len(raw), 64)]

def _addr(word: str) -> str:
    return "0x" + word[24:]

def _sig(words: list[str], w: int) -> str:
    # Order struct layout:
    # [w+12] = bytes offset (always 0x1a0)
    # [w+13] = length (0x41 = 65 bytes)
    # [w+14] = sig bytes  0..31
    # [w+15] = sig bytes 32..63
    # [w+16] = sig byte 64, zero-padded
    return "0x" + words[w+14] + words[w+15] + words[w+16][:2]

def _parse_order(words: list[str], w: int) -> dict:
    return {
        "salt":          str(int(words[w],    16)),
        "maker":         _addr(words[w+1]),
        "signer":        _addr(words[w+2]),
        "taker":         _addr(words[w+3]),
        "tokenId":       str(int(words[w+4],  16)),
        "makerAmount":   str(int(words[w+5],  16)),
        "takerAmount":   str(int(words[w+6],  16)),
        "expiration":    str(int(words[w+7],  16)),
        "nonce":         str(int(words[w+8],  16)),
        "feeRateBps":    str(int(words[w+9],  16)),
        "side":          str(int(words[w+10], 16)),
        "signatureType": str(int(words[w+11], 16)),
        "signature":     _sig(words, w),
    }


def parse_calldata(calldata_hex: str) -> dict:
    w = _words(calldata_hex)

    # Taker order
    taker_word  = int(w[0], 16) // 32
    taker_order = _parse_order(w, taker_word)

    # Maker orders array
    maker_arr   = int(w[1], 16) // 32
    n_makers    = int(w[maker_arr], 16)
    maker_orders = [
        _parse_order(w, maker_arr + 1 + int(w[maker_arr + 1 + i], 16) // 32)
        for i in range(n_makers)
    ]

    # makerFillAmounts
    fill_w  = int(w[4], 16) // 32
    n_fills = int(w[fill_w], 16)
    maker_fills = [str(int(w[fill_w + 1 + i], 16)) for i in range(n_fills)]

    # makerFeeAmounts
    fee_w  = int(w[6], 16) // 32
    n_fees = int(w[fee_w], 16)
    maker_fees = [str(int(w[fee_w + 1 + i], 16)) for i in range(n_fees)]

    return {
        "takerOrder":         taker_order,
        "makerOrders":        maker_orders,
        "takerFillAmount":    str(int(w[2], 16)),
        "takerReceiveAmount": str(int(w[3], 16)),
        "makerFillAmounts":   maker_fills,
        "takerFeeAmount":     str(int(w[5], 16)),
        "makerFeeAmounts":    maker_fees,
    }

def get_calldata(tx_hash):
    file_path = f"./data/hex_data/{tx_hash}.txt"

    if not os.path.exists(file_path):
        raise ValueError("file does not exist: ", file_path)
    
    with open(file_path, "r") as file:
        calldata = file.read()
    return calldata

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
    wallet = "0x63ce342161250d705dc0b16df89036c8e5f9ba9a"
    for hash in tx_hashes:
        json_logs = parse_calldata(get_calldata(hash))
        print(parse_json(json_logs, wallet))

if __name__ == "__main__":
    main()