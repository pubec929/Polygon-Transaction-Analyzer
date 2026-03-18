import requests
from datetime import datetime
from pytz import timezone
import json
import os

from typing import Dict, Tuple
from dataclasses import dataclass, asdict
import time

from pprint import pprint

BASE_PATH = "./data/market_id_maps"

@dataclass
class Market:
    id: str
    question: str
    slug: str
    conditionId: str
    endDate: str
    clobTokenIds: Tuple[str, str]
    option: str # either "up" or "down"

    def toJSON(self):
        return json.dumps(self.__dict__)

    def __str__(self):
        return json.dumps(self.__dict__)

def getMarketBySlug(slug):
    url = "https://gamma-api.polymarket.com/markets"
    params = {
        "slug": slug
    }
    response = requests.get(url, params)
    data = response.json()
    parsed = parseMarket(data[0])
    return parsed

def parseClobTokenIds(json_data: str) -> Tuple:
    positionId1, positionId2 = json_data.split(",")
    positionId1 = hex(int(positionId1[2:-1]))
    positionId2 = hex(int(positionId2[2:-2]))
    return (positionId1, positionId2)

def parseMarket(json_data: Dict):
    data = [
        json_data["id"],
        json_data["question"],
        json_data["slug"],
        json_data["conditionId"],
        json_data["endDate"],
        parseClobTokenIds(json_data["clobTokenIds"])
    ]
    #print(json_data["clobTokenIds"], type(json_data["clobTokenIds"]))
    return Market(*data, *["up"]), Market(*data, *["down"]) 

def parseMarketFromFile(json_data: Dict):
    data = [
        json_data["id"],
        json_data["question"],
        json_data["slug"],
        json_data["conditionId"],
        json_data["endDate"],
        json_data["clobTokenIds"],
        json_data["option"]
    ]
    return Market(*data)

def getLastTimestamp():
    year = datetime.now().year
    month = datetime.now().month
    day = datetime.now().day
    hour = datetime.now().hour
    calc_minute = datetime.now().minute // 5 * 5
    
    return str(datetime(year, month, day, hour, calc_minute).timestamp())[:-2]

def getLast15minTimestamp():
    year = datetime.now().year
    month = datetime.now().month
    day = datetime.now().day
    hour = datetime.now().hour
    calc_minute = datetime.now().minute // 15 * 15
    
    return str(datetime(year, month, day, hour, calc_minute).timestamp())[:-2]

def getActive5minMarketSlugs():
    base_slugs = ["btc-updown-5m-", "eth-updown-5m-", "sol-updown-5m-", "xrp-updown-5m-"]
    timestamp = getLastTimestamp()
    return [slug + timestamp for slug in base_slugs]

def getActive15MinMarketSlugs():
    base_slugs = ["btc-updown-15m-", "eth-updown-15m-", "sol-updown-15m-", "xrp-updown-15m-"]
    timestamp = getLast15minTimestamp()
    return [slug + timestamp for slug in base_slugs]

def getActiveHourlyMarketSlugs():
    base_slugs = ["bitcoin-up-or-down-", "ethereum-up-or-down-", "solana-up-or-down-", "xrp-up-or-down-"]
    months = {
        1: "january", 
        2: "february", 
        3: "march", 
        4: "april", 
        5: "may",
        6: "june", 
        7: "july", 
        8: "august", 
        9: "september", 
        10: "october", 
        11: "november", 
        12: "december"}
    tz = timezone("US/Eastern")
    month = months[datetime.now(tz).month]
    day = str(datetime.now(tz).day)
    year = datetime.now(tz).year

    hour = datetime.now(tz).hour
    suffix = "am"
    if hour > 11:
        suffix = "pm"
        if hour > 12:
            hour -= 12
    
    return [f"{slug}{month}-{day}-{year}-{hour}{suffix}-et" for slug in base_slugs]

def saveAsFile(path, markets):
    markets = {positionId: markets[positionId].toJSON() for positionId in markets}
    with open(path, "w") as file:
        json.dump(markets, file, indent=4)

def readFromFile(path):
    markets = {}
    with open(path, "r") as file:
        json_data = json.load(file)

    for positionId in json_data:
        #print(market_json)
        market_json = json.loads(json_data[positionId])
        markets[positionId] = parseMarketFromFile(market_json)

    return markets

def getIdMap() -> Dict[str, Market]:
    slugs = getMarketSlugs()
    #slugs = getActive15MinMarketSlugs()
    markets = {}
    for slug in slugs:
        marketUp, marketDown = getMarketBySlug(slug) 
        positionIdUp = marketUp.clobTokenIds[0]
        positionIdDown = marketDown.clobTokenIds[1]
        markets[positionIdUp] = marketUp
        markets[positionIdDown] = marketDown
    return markets

def getMarketSlugs():
    return [*getActive5minMarketSlugs(), *getActive15MinMarketSlugs(), *getActiveHourlyMarketSlugs()]

def createMarketMap():
    markets = getIdMap()
        
    lastTimeStamp = getLastTimestamp()
    file_path = f"{BASE_PATH}/marketIdMap-{lastTimeStamp}.json"
    saveAsFile(file_path, markets)
    return markets

def getFilePath(timestamp: str):
    return f"{BASE_PATH}/marketIdMap-{timestamp}.json"

def fetchIdMap():
    currTimeStamp = getLastTimestamp()

    lastTimeStamp = sorted(os.listdir("./data./market_id_maps"))[-1].split("-")[-1].replace(".json", "")
    print(currTimeStamp, lastTimeStamp)
    if lastTimeStamp == currTimeStamp:
        markets = readFromFile(getFilePath(currTimeStamp))
        print("read from file")
    else:
        
        markets = createMarketMap()
        print("created file")
        

    return markets

def main():
    # currTimeStamp = getLastTimestamp()
# 
    # lastTimeStamp = sorted(os.listdir(f"{BASE_PATH}/market_id_maps"))[-1].split("-")[-1].replace(".json", "")
    # print("starting...")
    # print("Current time: ", time.asctime(time.localtime()))
# 
    # markets = createMarketMap()
    # pprint(markets)
    # for id in markets:
    #    print(id, markets[id])
    print(getActive15MinMarketSlugs())
    print(getMarketBySlug("presidential-election-winner-2028"))
    # print(getMarketBySlug("btc-updown-15m-1770590700"))
    # if lastTimeStamp == currTimeStamp:
    #     markets = readFromFile(getFilePath(currTimeStamp))
    #     print("read from file")
    # else:
    #     markets = createMarketMap()
    #     print("updated")
    
    # print(markets)
        
    
    #readFromFile(file_path)
    # conditionIds = [market.conditionId for market in markets]
    # print(conditionIds)

if __name__ == "__main__":
    #main()
    ...
