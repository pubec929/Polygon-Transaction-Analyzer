import time
from utils.main import Colors, cprint
from datetime import datetime

class Trade:
    def __init__(self, tx_hash: str, usdc_amount: float, market_name: str, slug: str, conditionId: str, side: str, action: str, shares: float, detection_time: float, block_time: float):
        self.tx_hash = tx_hash
        self.usdc_amount = usdc_amount
        self.market_name = market_name
        self.slug = slug
        self.conditionId = conditionId
        self.side = side
        self.action = action
        self.shares = shares
        self.share_price = usdc_amount / shares
        self.block_time = block_time
        self.detection_time = detection_time

        self.detection_delay = detection_time - block_time
        self.processing_delay = time.time()  - detection_time
        self.total_delay = time.time() - block_time

    def display(self):
        market_color = ""
        side_color = ""
        action_color = ""

        if "Ethereum" in self.market_name:
            market_color = Colors.ETHEREUM
        elif "Bitcoin" in self.market_name:
            market_color = Colors.BITCOIN
        elif "XRP" in self.market_name:
            market_color = Colors.XRP
        elif "Solana" in self.market_name:
            market_color = Colors.SOLANA
        
        if self.side == "up":
            side_color = Colors.GREEN
        elif self.side == "down":
            side_color = Colors.RED

        if self.action == "BUY":
            action_color = Colors.BUY
        elif self.action == "SELL":
            action_color = Colors.SELL
        
        print(f"\n{'='*20}> TRADE DETECTED <{'='*20}")
        print(f"⚡ Tx: {self.tx_hash}")
        print(f"💰 ${self.usdc_amount:.2f} | {cprint(self.action, action_color)}")
        print(f"📊 {cprint(self.market_name, market_color)} | {cprint(self.side, side_color)}")
        print(f"〽️ Shares: {self.shares:.1f} | Price per share: {self.share_price * 100: .0f}¢")
        print(f"⏱️  Detection delay: {self.detection_delay:.3f}s | Processing: {self.processing_delay:.3f}s | Total delay: {self.total_delay:.3f}s")
        print(f" Block time: {datetime.fromtimestamp(self.block_time)}")
        print(f" Detection time: {datetime.fromtimestamp(self.detection_time)}")
        print(f" Current time: {datetime.now()}")
        print("=" * 80)

type Trades = list[Trade]