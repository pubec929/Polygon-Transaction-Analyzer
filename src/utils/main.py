import requests
import os
from dotenv import load_dotenv
from datetime import datetime
import pytz

load_dotenv()
ALCHEMY_API_KEY = os.getenv("ALCHEMY_API_KEY") or ""

def getBalance(wallet: str) -> float:
    url = f"https://polygon-mainnet.g.alchemy.com/v2/{ALCHEMY_API_KEY}"
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "alchemy_getTokenBalances",
        "params": [
            wallet,
            ["0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"],
        ]
    }

    response = requests.post(url, json=payload).json()
    if "result" not in response:
        return -1.0
    
    balance = response["result"]["tokenBalances"][0]["tokenBalance"]
    return int(balance, 16) / 1_000_000

def getAllPositionsValue(wallet):
    url = "https://data-api.polymarket.com/positions"
    params = {
        "user": wallet,
        "limit": 500
    }
    response = requests.get(url, params).json()
    total_amount = 0
    for position in response:
        total_amount += position["currentValue"]
    return total_amount

def get_start_time_timestamp(start_time):
    year = datetime.now().year
    month = datetime.now().month
    day = datetime.now().day

    return datetime.strptime(f"{day}/{month}/{year} {start_time}", "%d/%m/%Y  %H:%M:%S").timestamp()

def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')

def get_property(collection, property: str):
    properties = []
    for item in collection:
        properties.append(getattr(item, property))
    return properties
# everythin related to color printing
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    ORANGE = "\x1b[38;5;214m"
    PINK = "\x1b[38;5;219m"
    ETHEREUM = "\x1b[38;5;27m"
    BITCOIN = "\x1b[38;5;214m"
    SOLANA = "\x1b[38;5;56m"
    XRP = "\x1b[38;5;33m"
    BUY = "\x1b[38;2;58;150;221m"
    SELL = "\x1b[38;2;180;0;158m"

def cprint(msg, color):
    END = "\033[0m"
    return f"{color}{msg}{END}"

def get_timestamp_from_slug(slug: str):
    months = { "january": 1,  "february": 2, "march": 3, "april": 4, 
               "may": 5, "june": 6, "july": 7, "august": 8, 
               "september": 9, "october": 10, "november": 11, "december": 12}

    if "5m" in slug or "15m" in slug:
        *_, timestamp = slug.split("-")
        return int(timestamp)
    elif "pm" in slug or "am" in slug:
        year = datetime.now().year
        *_, month, day, hour, tz = slug.split("-")

        hour = int(hour[:-2]) if hour[-2:] == "am" else (int(hour[:-2]) + 12) % 24
        #print(hour)
        date = datetime.strptime(f"{day}/{months.get(month)}/{year} {hour}:00:00", "%d/%m/%Y %H:%M:%S")

        eastern = pytz.timezone("US/Eastern")
        date_eastern = eastern.localize(date)  # attach ET timezone
        date_utc = date_eastern.astimezone(pytz.utc)  # convert to UTC

        return int(date_utc.timestamp())