import time
import json
from datetime import datetime

from hex_parser import parse_json, parse_calldata


class MempoolTransaction:
    def __init__(self, tx_hash, sender, receiver, data):
        self.tx_hash = tx_hash
        self.sender = sender
        self.receiver = receiver
        self.data = data
        self.timestamp = time.time()

    def __str__(self):
        return json.dumps(self.__dict__)


async def process_pending_transaction(wallet, tx_data: dict, id_map):
        """Process a pending (mempool) transaction"""
        
        detection_time = time.time()
        
        try:
            tx_hash = tx_data.get('hash', "")
            from_addr = tx_data.get('from', '').lower()
            to_addr = tx_data.get('to', '').lower()
            input_data = tx_data.get('input', '')
            transaction = MempoolTransaction(tx_hash, from_addr, to_addr, input_data)
        
            if not input_data or len(input_data) < 10:
                pass

            if wallet[2:]  not in input_data:
                return
            # Try to extract token ID
            transaction = parse_json(parse_calldata(input_data), wallet)[0]
            token_id = transaction.position_id
            
            # Try to estimate USDC amount
            usdc_amount = transaction.usdc_amount
            shares = transaction.shares
            
            if not token_id and not usdc_amount:
                print(f"⚠️  Could not decode transaction: {tx_hash[:20]}...")
                return 
            
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

