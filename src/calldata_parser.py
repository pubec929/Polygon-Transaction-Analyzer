"""
Polymarket CTF Exchange - matchOrders Calldata Parser
Parses raw calldata hex into the Polymarket API JSON structure.
"""
import json
import os


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


def parse_match_orders(calldata_hex: str) -> dict:
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
    
    print(file_path)
    with open(file_path, "r") as file:
        calldata = file.read()
    print(calldata)
    return calldata
    


if __name__ == "__main__":
    tx_hashes = [
    "0x83a21e2c5f90953160fc6ca2d9c9d7b6af2ad237a27c124164504fb3ab9a7d89",
    "0x352533202b58c02472f9cf27ed52b5d068ef688a96bc9781520172d13b27f60b",
    "0x8285fe61f9ece8edf041637796f3f99032f3fcc3a7f45519cb03144dafb795aa",
    "0xb73355dafd113db35277f504a640c4b857d639a8fe60c5ddef4df95d03143bef",
    "0xf5968ac8dce8b05b963bfa4ededbbf4dc0e05c4db49e106260ad0faf46116c51",
    "0x19cd48b48142a95cdf4ceb2b71d39e2b870f45a7cc098378bac50c5c4b2d1b2a", 
    "0x9c6e047c6ccfc349d80bc875d827fb2522698b180de6f1e8d80736f982dee624"]

    tx_hash = tx_hashes[-4]
    calldata = get_calldata(tx_hash)
    result = parse_match_orders(calldata)
    print(json.dumps(result, indent=2))