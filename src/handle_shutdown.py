import json
import time

from utils.main import get_timestamp_from_slug
from trade import Trades

FILE_PATH = "./data/trade_logs"

class Position: 
    def __init__(self, market_name, slug, conditionId, side, shares, usdc_amount, bought_shares, bought_usdc_amount, sold_shares, sold_usdc_amount, total_num_trades, num_buy_trades, num_sell_trades):
        self.market_name = market_name
        self.market_slug = slug
        self.conditionId = conditionId
        self.side = side
        self.shares = shares
        self.usdc_amount = usdc_amount

        self.bought_shares = bought_shares
        self.bought_usdc_amount = bought_usdc_amount

        self.sold_shares = sold_shares
        self.sold_usdc_amount = sold_usdc_amount

        self.total_num_trades = total_num_trades
        self.num_buy_trades = num_buy_trades
        self.num_sell_trades = num_sell_trades

    @property
    def price_per_share(self):
        return self.usdc_amount / self.shares if self.shares != 0 else 0.0
    
    def display(self):
        msg = f"{"=" * 20} Positions {"=" * 20}"
        print(len(msg))
        print(f"Market name: {self.market_name} | {self.side}")
        print(f"conditionId: {self.conditionId}")
        print(f"usdc amount: ${self.usdc_amount: .2f} | shares: {self.shares}")
        print(f"price per share: {self.price_per_share: .12}¢")
        print("=" * len(msg))
        print(f"Number of bought shares: {self.bought_shares}")
        print(f"Bought usdc amouont: {self.bought_usdc_amount}")
        print("=" * len(msg))
        print(f"Number of sold shares: {self.sold_shares}")
        print(f"sodl usdc amount: {self.sold_usdc_amount}")
        print("=" * len(msg))
        print(f"Total number of trades: {self.total_num_trades}")
        print(f"Number of buy trades: {self.num_buy_trades}")
        print(f"Number of sell trades: {self.num_sell_trades}")
        print("=" * len(msg))

def calc_positions(trades: Trades):
        positions: Positions = {}
        for trade in trades:
            trade_hash = hash(trade.market_name + trade.side)
            if trade_hash not in positions:
                positions[trade_hash] = Position(trade.market_name, trade.slug, trade.conditionId, trade.side, 0, 0, 0, 0, 0, 0, 0, 0, 0)

            position = positions[trade_hash]
            position.total_num_trades += 1
            if trade.action == "BUY":
                position.shares += trade.shares
                position.usdc_amount += trade.usdc_amount

                position.bought_shares += trade.shares
                position.bought_usdc_amount += trade.usdc_amount
                position.num_buy_trades += 1
            elif trade.action == "SELL":
                position.shares -= trade.shares
                position.usdc_amount -= trade.usdc_amount

                position.sold_shares += trade.shares
                position.sold_usdc_amount += trade.usdc_amount
                position.num_sell_trades += 1
    
        return positions

type Positions = dict[int, Position]

def shutdown(trades: Trades = []):
    print("shutting down gracefully")

    positions = calc_positions(trades)
    for pos in positions.values():
        pos.display()
   

    print("Number of trades: ", len(trades))
    print("Number of positions: ", len(positions))

    json_data: list[str] = [json.dumps(trade.__dict__) for trade in trades]

    timestamp = get_timestamp_from_slug(trades[0].slug)
    with open(f"{FILE_PATH}/{timestamp}-session.json", mode="w", encoding="utf-8") as file:
        json.dump(json_data, file, indent=4)

    print(f"Saved {len(trades)} trade logs successfully")