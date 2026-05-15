import os
import json
import time
import asyncio
from datetime import datetime

from websockets import connect

from handle_shutdown import shutdown
from utils.main import *
from utils.market_filter import MarketFilter
from marketIdMapper import getIdMap, getLastTimestamp
from mempoolMonitor import MempoolTransaction
from hex_parser import parse_json, parse_calldata

from dataclasses import dataclass
from typing import Literal

Market = Literal["bitcoin", "ethereum", "solana", "xrp"]
FilterType = Literal["5min", "15min", "60min"]


load_dotenv()

ALCHEMY_API_KEY = os.getenv("ALCHEMY_API_KEY") or ""
WSS_URL = f"wss://polygon-mainnet.g.alchemy.com/v2/{ALCHEMY_API_KEY}"

@dataclass
class Settings:
    duration: int
    wallet: str
    scheduledStart: bool
    startTime: str
    activeFilter: bool
    filterMarket: Market
    filterType: FilterType

class TradeMonitor:
    def __init__(self, settings_path, processMessage, onSetup, onShutdown, subscriptions):
        self.settings = self.load_settings(settings_path)

        self.processMessage = processMessage
        self.onSetup = onSetup
        self.onShutdown = onShutdown
        self.subscriptions = subscriptions

    async def setup(self):
        self.websocket = await self.onSetup(self.settings, self.subscriptions)
        await self.loop(self.settings.wallet, self.settings.duration)

    async def loop(self, wallet, duration):
        print(datetime.now())
        print("\nLIVE - Waiting for trades...")
        print("=" * 80)
        
        running = True
        idMap = getIdMap()
        currentTimeStamp = getLastTimestamp()
        #market_filter.setTargetIds(idMap)
        message_count = 0
        boot_time = time.time()
        while running:
            message = await self.websocket.recv()
            message_count += 1
            
            # Print every 10th message to show we're getting data
            if message_count % 10 == 0:
                print(f"📡 Received {message_count} messages...")
            
            message = json.loads(message)
            await self.processMessage(wallet, message, idMap)
            

            # stop condition
            if time.time() - boot_time >= duration: #or len(trades) >= 50:
                running = False

    def shutdown(self):
        self.onShutdown()

    def load_settings(self, file_path: str) -> Settings:
        if not os.path.exists(file_path):
            raise ValueError(f"file doesn't exist, {file_path}")

        with open(file_path, "r") as f:
            settings_json = json.load(f)

        settings = Settings(**settings_json)
        return settings

async def setting_up(settings: Settings, subscriptions):
    wallet = settings.wallet
    clear_console()

    print("Initializing...")
    print(f"Monitoring trades from: {wallet}")
    print(f"wallet balance: ${getBalance(wallet):,.2f}")
    print(f"positions value: ${getAllPositionsValue(wallet):,.2f}")
    print("=" * 80)
    
    market_filter = MarketFilter(settings.filterMarket, settings.filterType, getIdMap(), settings.activeFilter)
    if market_filter.active: print("✅ Filter is active")
    else: print("❌ Filter is not active")

    if settings.scheduledStart:
        start_time_timestamp = get_start_time_timestamp(settings.startTime)
        if start_time_timestamp < time.time():
            raise ValueError("Invalid starting time! Adjust or deactivate scheduled start")
        print("Scheduled start at: " + settings.startTime)
        print(f"Expected runtime: {settings.duration}s")
        while start_time_timestamp > time.time():
            time.sleep(0.1)

    websocket = await connect(WSS_URL)
    for sub in subscriptions:
        await websocket.send(json.dumps(sub))
        response = await websocket.recv()
        print(f"✅ Subscribed to websocket")
        print(f"   Response: {response}")
    
    return websocket

subscriptions = [{
            "jsonrpc": "2.0",
            "id": 1,
            "method": "eth_subscribe",
            "params": [
                "alchemy_pendingTransactions", 
                { "toAddress": "0xe3f18acc55091e2c48d883fc8c8413319d4ab7b0" }
            ]
        }]
monitor = TradeMonitor("./src/settings.json", process_message, setting_up, shutdown, subscriptions)
asyncio.run(monitor.setup())
