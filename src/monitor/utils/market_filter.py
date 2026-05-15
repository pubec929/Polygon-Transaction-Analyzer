class MarketFilter:
    def __init__(self, market_name, market_type, idMap, active=True):
        self.market_name = market_name
        self.market_type = market_type
        self.active = active
        self.target_ids: tuple[str, str] 
        self.setTargetIds(idMap)

    def setTargetIds(self, idMap):
        if not self.active: 
            return
        target_ids = ("", "")
        name_filter = ""
        type_filter = ""

        # setting the filter params
        if self.market_type == "5min" or self.market_type == "15min":
            name_map = {
                "bitcoin": "btc",
                "ethereum": "eth",
                "solana": "sol",
                "xrp": "xrp"
            }
            name_filter = name_map.get(self.market_name.lower(), "")
            type_filter = "-" + self.market_type.replace("in", "") + "-"
            
        elif self.market_type == "60min":
            name_filter = self.market_name.lower()
            type_filter = ("pm", "am")

        # filtering  
        for market in idMap.values():
                if type(type_filter) == str:
                    if name_filter in market.slug and type_filter in market.slug:
                        target_ids = market.clobTokenIds
                        break
                else:
                    if name_filter in market.slug and (type_filter[0] in market.slug or type_filter[1] in market.slug):
                        target_ids = market.clobTokenIds
                        break

        # error message
        if target_ids == ("", ""):
            raise ValueError(
                f"Coudn't find matching market. Invalid filter parameters: {self.market_name, self.market_type}")
        # successfull
        else:
            print("Set filter parameters succesfully")
            self.target_ids = target_ids