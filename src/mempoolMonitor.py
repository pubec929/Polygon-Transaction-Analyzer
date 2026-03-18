from web3 import Web3
import requests
from websockets import connect
import asyncio
import json
import time
from datetime import datetime

from typing import Literal, Set, Dict
from dataclasses import dataclass
from pprint import pprint

from dotenv import load_dotenv
import os
import sys

from marketIdMapper import getIdMap, getLastTimestamp
from log_parser import analyze_logs, Transactions
from handle_shutdown import shutdown
from trade import Trade, Trades

from utils.main import getAllPositionsValue, getBalance, get_start_time_timestamp, Colors, cprint, clear_console
from utils.market_filter import MarketFilter

from hex_parser import parse_calldata, parse_json


load_dotenv()

ALCHEMY_API_KEY = os.getenv("ALCHEMY_API_KEY") or ""
URL = f"https://polygon-mainnet.g.alchemy.com/v2/{ALCHEMY_API_KEY}"
WSS_URL = f"wss://polygon-mainnet.g.alchemy.com/v2/{ALCHEMY_API_KEY}"
POLYMARKET_URL = "https://data-api.polymarket.com/positions"

# WALLET = "0xe00740bce98a594e26861838885ab310ec3b548c"
WALLET = "0x63ce342161250d705dc0b16df89036c8e5f9ba9a"
WALLET_PADDED = f"000000000000000000000000{WALLET[2:]}"

# Polymarket contract addresses
CTF_EXCHANGE = "0x4bFb41d5B3570DeFd03C39a9A4D8dE6Bd8B8982E"
CONDITIONAL_TOKENS = "0x4D97DCd97eC945f40cF65F87097ACe5EA0476045"
USDC_CONTRACT = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"

FEE_MODULE_ADDRESS = "0xE3f18aCc55091e2c48d883fc8C8413319d4Ab7b0"

# Event signatures
TRANSFER_ERC20 = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
TRANSFER_SINGLE = "0xc3d58168c5ae7397731d063d5bbf3d657854427343f4c083240f7aacaa2d0f62"

# Function signatures for Polymarket
FILL_ORDER_SIG = "0x0ca84946"  # fillOrder(Order,uint256,bytes)
MATCH_ORDERS_SIG = "0x88d7f51b"  # matchOrders(Order,Order,bytes,bytes)

DURATION = 5*60+1 # time in seconds


trades: Trades = []
seen_pending_txs = []
class MempoolTransaction:
    def __init__(self, tx_hash, sender, receiver, data):
        self.tx_hash = tx_hash
        self.sender = sender
        self.receiver = receiver
        self.data = data
        self.timestamp = time.time()
        self.foundWallet = WALLET in data

    def __str__(self):
        return json.dumps(self.__dict__)

class MempoolMonitor:
    def __init__(self, target_wallet: str, market_id_map: Dict):
        self.target_wallet = target_wallet.lower()
        self.market_id_map = market_id_map
        self.known_token_ids = set(market_id_map.keys())
        
        # Track what we've seen
        self.seen_pending_txs: Set[str] = set()
        self.seen_mined_txs: Set[str] = set()
        self.mempool_txs= set()
        
        self.mempool_transactions = {}
        # Statistics
        self.stats = {
            'pending_detected': 0,
            'pending_relevant': 0,
            'mined_detected': 0,
            'mempool_time_samples': [],
            'total_latency_saved': 0
        }
    
    async def process_pending_transaction(self, tx_data: Dict):
        """Process a pending (mempool) transaction"""
        
        detection_time = time.time()
        
        try:
            tx_hash = tx_data.get('hash', "")
            self.mempool_txs.add(tx_hash)
            from_addr = tx_data.get('from', '').lower()
            to_addr = tx_data.get('to', '').lower()
            input_data = tx_data.get('input', '')
            transaction = MempoolTransaction(tx_hash, from_addr, to_addr, input_data)
            self.mempool_transactions[tx_hash] = transaction
            # print(from_addr)
            # print(tx_hash)
            # print(input_data)
            # exit()
            # Quick filters
            if tx_hash in self.seen_pending_txs:
                pass
                #return
            
            # Check if it's going to Polymarket contracts
            #if to_addr not in [CTF_EXCHANGE.lower(), CONDITIONAL_TOKENS.lower()]:
            #    return
            
            self.seen_pending_txs.add(tx_hash)
            self.stats['pending_detected'] += 1
            
            # Check function signature
            if not input_data or len(input_data) < 10:
                pass
                #return
            
            func_sig = input_data[:10]
            
            #if func_sig not in [FILL_ORDER_SIG, MATCH_ORDERS_SIG]:
            #    print(f"⚠️  Unknown function: {func_sig}")
               # return
            
            print(tx_hash)
            if "63ce342161250d705dc0b16df89036c8e5f9ba9a"  not in input_data:
                #print("didnt find it")
                #print(input_data)
                return
            else:
                #print(transaction)
                print("found it!!!!!!!!!!")
            # Try to extract token ID
            transaction = parse_json(parse_calldata(input_data), WALLET)[0]
            token_id = transaction.position_id
            
            # Try to estimate USDC amount
            usdc_amount = transaction.usdc_amount
            shares = transaction.shares
            
            if not token_id and not usdc_amount:
                print(f"⚠️  Could not decode transaction: {tx_hash[:20]}...")
                #return
            
            self.stats['pending_relevant'] += 1
            
            # Get market info
            market_name = "Unknown Market"
            option = "Unknown"
            
            if token_id and token_id in self.market_id_map:
                market_name = self.market_id_map[token_id].question
                option = self.market_id_map[token_id].option
            

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
            self.pending_transactions = getattr(self, 'pending_transactions', {})
            self.pending_transactions[tx_hash] = {
                'detection_time': detection_time,
                'token_id': token_id,
                'usdc_amount': usdc_amount,
                'market_name': market_name,
                'option': option
            }
            
        except Exception as e:
            print(f"❌ Error processing pending tx: {e}")
            import traceback
            traceback.print_exc()

w3 = Web3(Web3.HTTPProvider(URL, request_kwargs={"timeout": 30}))
async def monitor_trades():
    clear_console()

    print("Initializing...")
    currentTimeStamp = getLastTimestamp()
    idMap = getIdMap()
    print(f"Monitoring trades from: {WALLET}")
    print(f"wallet balance: ${getBalance(WALLET):,.2f}")
    print(f"positions value: ${getAllPositionsValue(WALLET):,.2f}")
    print("=" * 80)
    
    seen_txs = set()
    active_task = set()
    message_count = 0

    market_filter = MarketFilter("bitcoin", "5min", idMap, False)
    if market_filter.active: print("✅ Filter is active")
    else: print("❌ Filter is not active")
    #trades: List[Trade] = []

    if len(sys.argv) == 1:
        isStartScheduled = False
        start_time = ""
    else:
        isStartScheduled = True
        start_time = sys.argv[1]
    
    if isStartScheduled:
        start_time_timestamp = get_start_time_timestamp(start_time)
        if start_time_timestamp < time.time():
            raise ValueError("Invalid starting time! Adjust or deactivate scheduled start")
        print("Scheduled start at: " + start_time)
        print(f"Expected runtime: {DURATION}s")
        while start_time_timestamp > time.time():
            time.sleep(0.1)

    boot_time = time.time()

    monitor = MempoolMonitor(WALLET, idMap)
    async with connect(WSS_URL) as websocket:
        pending_subscription = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "eth_subscribe",
            "params": [
                "alchemy_pendingTransactions", 
                { "toAddress": "0xe3f18acc55091e2c48d883fc8c8413319d4ab7b0" }
            ]
        }
        
        await websocket.send(json.dumps(pending_subscription))
        response1 = await websocket.recv()
        print(f"✅ Subscribed to PENDING transactions (mempool)")
        print(f"   Response: {response1}\n")

  
        print(datetime.now())
        print("\nLIVE - Waiting for trades...")
        print("=" * 80)
        
        running = True
        idMap = getIdMap()
        currentTimeStamp = getLastTimestamp()
        market_filter.setTargetIds(idMap)
        #trades: List[Trade] = []
        while running:
            try:
                message = await websocket.recv()
                message_count += 1
                
                # Print every 10th message to show we're getting data
                if message_count % 10 == 0:
                    print(f"📡 Received {message_count} messages...")
                
                data = json.loads(message)

                if "params" in data and "result" in data["params"]:
                    result = data["params"]["result"]
                    
                    # Check if it's a pending transaction (from mempool)
                    if "hash" in result and "from" in result and "input" in result:
                        # This is a full transaction object (pending)
                        # print("mempool", print(result))
                        # print("mempool")
                        await monitor.process_pending_transaction(result)
    
                # stop condition
                if time.time() - boot_time >= DURATION: #or len(trades) >= 50:
                    running = False
                
            # error handling      
            except Exception as e:
                print(f"Error: {e}")
                import traceback
                traceback.print_exc()
                await asyncio.sleep(1)

        shutdown(trades)
if __name__ == "__main__":
    asyncio.run(monitor_trades())