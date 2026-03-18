from dotenv import load_dotenv
import os
from web3 import Web3

from pprint import pprint
from dataclasses import dataclass
from typing import Literal

from typing import List, Literal
from dataclasses import dataclass

logTypeMap = {
    "d0a08e8c493f9c94f29311604c9de1b4e8c8d4c06bd0c789af57f2d65bfec0f6": "OrderFilled",
    "c3d58168c5ae7397731d063d5bbf3d657854427343f4c083240f7aacaa2d0f62": "TransferSingle",
    "ddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef": "Transfer",
    "8c5be1e5ebec7d5bd14f71427d1e84f3dd0314c0f7b2291e5b200ac8c7c3b925": "Approval",
    "b608d2bf25d8b4b744ba23ce2ea9802ea955e216c064a62f42152fbf98958d24": "FeeCharged",
    "b608d2bf25d8b4b744ba23ce2ea9802ea955e216c064a62f42152fbf98958d24": "FeeRefunded"
}

type Action = Literal["BUY", "SELL"]
type Logs = list[Log]
type Transactions= dict[str, Transaction]

@dataclass
class Log:
    address: str
    logIndex: int
    eventType: str
    topics: List[str]
    data: str

@dataclass
class Transaction:
    position_id: str
    action: Action
    usdc_amount: float
    shares: float
    
class OrderFilledEvent:
    def __init__(self, data: str):
        values = []
        for i in range(len(data) // 64):
            values.append(data[i * 64:(i+1)*64])

        self.makerAssetId = values[0]
        self.takerAssetId = values[1]
        self.makerAmountFilled = values[2]
        self.takerAmountFilled = values[3]
        self.fee = values[4]

class FeeRefundedEvent:
    def __init__(self, data: str):
        self.id = data[0:64]
        self.refund = data[64:]

def filterLogs(logs: list[dict], target: str) -> list[dict]:
    filtered_logs: list[dict] = []
    for log in logs:
        if any({str(address.hex()) == target for address in log["topics"][0:3]}):
            filtered_logs.append(log)
    return filtered_logs

def parseLogs(logs: list[dict]) -> Logs:
    parsed_logs: Logs = []
    important_keys = ["address", "logIndex", "eventType", "topics", "data"]
    for log in logs:
        values = {}
        print("hello", log)
        for key in log:
            val = log[key]
            if key == "data":
                values[key] = str(val.hex())
            elif key == "topics":
                event = str(val[0].hex())
                if event not in logTypeMap:
                    values["eventType"] = "Unknown"
                else:
                    values["eventType"] = logTypeMap[event]
                values[key] = [str(elem.hex()) for elem in val]
            elif key in important_keys:
                values[key] = val
        parsed_logs.append(Log(**values)) 
    return parsed_logs


def analyze_logs(logs, wallet) -> Transactions:
    PADDING = 1_000_000
    logs = parseLogs(filterLogs(logs, wallet)) # type: ignore

    transactions: Transactions = {}
    fee_refunds = {}
    for log in logs:
        if log.eventType == "OrderFilled":
            order_hash = log.topics[1]
            order = OrderFilledEvent(log.data)

            makerAssetId = int(order.makerAssetId, 16)
            takerAssetId = int(order.takerAssetId, 16)
            
            fee = int(order.fee, 16) / PADDING
            if makerAssetId == 0:
                action: Action = "BUY"
                position_id = takerAssetId
                usdc_amount = int(order.makerAmountFilled, 16) / PADDING
                shares = int(order.takerAmountFilled, 16) / PADDING
                shares = shares - fee
            if takerAssetId == 0:
                action: Action = "SELL"
                position_id = makerAssetId
                usdc_amount = int(order.takerAmountFilled, 16) / PADDING
                shares = int(order.makerAmountFilled, 16) / PADDING
                usdc_amount = usdc_amount - fee
            transactions[order_hash] = Transaction(hex(position_id), action, usdc_amount, shares) # type: ignore
        if log.eventType == "FeeRefunded":
            order_hash = log.topics[1]
            event = FeeRefundedEvent(log.data)
            fee_refunds[order_hash] = int(event.refund, 16) / PADDING

    # apply fee_refunds
    for order_hash, refund in fee_refunds.items():
        if order_hash in transactions:
            if transactions[order_hash].action == "SELL":
                transactions[order_hash].usdc_amount += refund
            elif transactions[order_hash].action == "BUY":
                transactions[order_hash].shares += refund        
    return transactions


load_dotenv()
ALCHEMY_API_KEY = os.getenv("ALCHEMY_API_KEY")
URL = f"https://polygon-mainnet.g.alchemy.com/v2/{ALCHEMY_API_KEY}"
# WALLET_PADDED = "000000000000000000000000e00740bce98a594e26861838885ab310ec3b548c"
WALLET = "63ce342161250d705dc0b16df89036c8e5f9ba9a"
WALLET_PADDED = "00000000000000000000000063ce342161250d705dc0b16df89036c8e5f9ba9a"


# TX_HASH = "0xfdc3738bdaa8272f8f6a08af7d91b0c346521432d26de08869d85e6c4f24867e"
# TX_HASH = "0xef7af668445df9abccc63f89d8de956d91baca746ba9bb76df4fd2d532c0f1ec"
TX_HASH = "0xefaf38f9db94679be62e55bbfd0f89746e9c386ae80a7780b9628fea17eb824a"
# TX_HASH = "0xf5968ac8dce8b05b963bfa4ededbbf4dc0e05c4db49e106260ad0faf46116c51"
TX_HASH = "0xb73355dafd113db35277f504a640c4b857d639a8fe60c5ddef4df95d03143bef"
# TX_HASH = "0x1fbbc68d2f04ff890d24bc095f937334df33b7b7b4f8de4716b16c29572cb197"
# TX_HASH = "0x9b63e6013129051022fdb75b1476c33a1a843a3867751ecca9ffdf60fd95a508"
# TX_HASH = "0x987e498d0d00c0584741df3ffc3aff945bbd826d0fd6966701cb98ad78e53651"

# TX_HASH = "0xbe71a9e319efe3c6666755d6af7b78d789044c08689c7d627cc472bc38820742" # falsch
#0xd5a937f16f1ba89b832a9b1e0da0975ff127d976bdfd701266f9082dae474b15 richtig
# TX_HASH = "0x2e2c327ea99d9e976c6551594e037ccfdd037f6d33810bd57757c4ad8ccfafe4" #richtig: 25.66 falsch: 26.00

# TX_HASH = "0x63bf27fc702858582c9dc40bf7987ca3ead225cc992f1a3cc06e61f9e51a84b6" #shares: 39.6 nicht 40


# TX_HASH = "0xefc4abebea43ab3fba34e3afdf7add14a487ef84bfde4a49ee9a942be23ce9a2" # falsch: 18
# TX_HASH = "0xef9ea3674c555bf8d472914917b248f9a0f6acb3786c3d39e11d1669f9cab682" # shares: 14.7 usdc: 4.93
# TX_HASH = "0x41decbc2d14c3dcf54dec54925c33be8916e443d19ec948fc96e0c8631b65ef8" # shares: 4.9 usdc: 1.55

tx_hashes = [
    "0x83a21e2c5f90953160fc6ca2d9c9d7b6af2ad237a27c124164504fb3ab9a7d89",
    "0x352533202b58c02472f9cf27ed52b5d068ef688a96bc9781520172d13b27f60b",
    "0x8285fe61f9ece8edf041637796f3f99032f3fcc3a7f45519cb03144dafb795aa",
    "0xb73355dafd113db35277f504a640c4b857d639a8fe60c5ddef4df95d03143bef",
    "0xf5968ac8dce8b05b963bfa4ededbbf4dc0e05c4db49e106260ad0faf46116c51",
    "0x19cd48b48142a95cdf4ceb2b71d39e2b870f45a7cc098378bac50c5c4b2d1b2a", 
    "0x9c6e047c6ccfc349d80bc875d827fb2522698b180de6f1e8d80736f982dee624",
    "0x4bd35242c6978fccd220f6c1ad3ade6e584a8efe5194ecab3c1973f7cf1bea04",
    "0x3f3bbf719ac8d16a49b27a82302edf37b34129a9ded55aea1589bd1f121a5d60",
    "0x4e77baa3e53b69ddb885dca032791a0009ee43ad9a8b24a5bd6f6bdc940000ff",
    "0xa8839bd0033f413e61fdd2cfd9f81f02975ed90cb242c5eb07e9e2009a615f62",
    "0x0949003f1fb592d83d88e8d4e2aba528282b43e3cf55d25219f6832415e98879"]

TX_HASH = tx_hashes[-1]

def main():
    w3 = Web3(Web3.HTTPProvider(URL, request_kwargs={"timeout": 30}))
    logs = w3.eth.get_transaction_receipt(TX_HASH).logs # type: ignore
    # print(logs)
    transactions = analyze_logs(logs, WALLET_PADDED)
    pprint(transactions)

if __name__ == "__main__":
    main()