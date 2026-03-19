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

async def process_pending_transaction(wallet, tx_data: dict, id_map):
        """Process a pending (mempool) transaction"""
        
        detection_time = time.time()
        
        try:
            tx_hash = tx_data.get('hash', "")
            from_addr = tx_data.get('from', '').lower()
            to_addr = tx_data.get('to', '').lower()
            input_data = tx_data.get('input', '')
            transaction = MempoolTransaction(tx_hash, from_addr, to_addr, input_data)
        
            # print(from_addr)
            # print(tx_hash)
            # print(input_data)
            # exit()
            # Quick filters
            """
            if tx_hash in self.seen_pending_txs:
                pass
                #return
            """
            # Check if it's going to Polymarket contracts
            #if to_addr not in [CTF_EXCHANGE.lower(), CONDITIONAL_TOKENS.lower()]:
            #    return
            
            # Check function signature
            if not input_data or len(input_data) < 10:
                pass
                #return
            #if func_sig not in [FILL_ORDER_SIG, MATCH_ORDERS_SIG]:
            #    print(f"⚠️  Unknown function: {func_sig}")
               # return
            
            print(tx_hash)
            if wallet[2:]  not in input_data:
                #print("didnt find it")
                #print(input_data)
                return
            else:
                #print(transaction)
                print("found it!!!!!!!!!!")
            # Try to extract token ID
            transaction = parse_json(parse_calldata(input_data), wallet)[0]
            token_id = transaction.position_id
            
            # Try to estimate USDC amount
            usdc_amount = transaction.usdc_amount
            shares = transaction.shares
            
            if not token_id and not usdc_amount:
                print(f"⚠️  Could not decode transaction: {tx_hash[:20]}...")
                #return
            
            #self.stats['pending_relevant'] += 1
            
            # Get market info
            market_name = "Unknown Market"
            option = "Unknown"
            
            if token_id and token_id in id_map:
                market_name = id_map[token_id].question
                option = id_map[token_id].option
            

            print(f"\n{'='*70}")
            print(f"🔥 MEMPOOL TRANSACTION DETECTED!")
            print(f"{'='*70}")
            print(f"⚡ Hash: {tx_hash}")
            print(f"📊 Market: {market_name[:50]}")
            print(f"🎯 Side: {option}")
            if usdc_amount:
                print(f"💰 Estimated amount: ${usdc_amount:.2f}")
            if shares:
                print(f"Number of shares: {shares}")
            if token_id:
                print(f"🎫 Token ID: {token_id}")
            print(f"⏱️  Detection time: {datetime.now().strftime('%H:%M:%S.%f')[:-3]}")
            print(f"🚀 STATUS: PENDING (not yet mined)")
            print(f"{'='*70}\n")
            print(transaction)
            # Store for later comparison
            """
            self.pending_transactions = getattr(self, 'pending_transactions', {})
            self.pending_transactions[tx_hash] = {
                'detection_time': detection_time,
                'token_id': token_id,
                'usdc_amount': usdc_amount,
                'market_name': market_name,
                'option': option
            }
            """
            
        except Exception as e:
            print(f"❌ Error processing pending tx: {e}")
            import traceback
            traceback.print_exc()

async def process_message(wallet, data, id_map):
    if "params" in data and "result" in data["params"]:
        result = data["params"]["result"]
        
        # Check if it's a pending transaction (from mempool)
        if "hash" in result and "from" in result and "input" in result:
            # This is a full transaction object (pending)
            # print("mempool", print(result))
            # print("mempool")
            await process_pending_transaction(wallet, result, id_map)


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
