import os
import json

from handle_shutdown import shutdown

class MarketFilter:
    def __init__(self, isActive: bool, market: str, market_type: str):
        self.is_active = isActive
        self.market = market
        self.market_type = market_type

class ScheduledStart:
    def __init__(self, isActive: bool, startTime: str):
        self.is_active = isActive
        self.start_time = startTime

class Settings:
    def __init__(self, duration: int, wallet: str, scheduledStart: dict, marketFilter: dict):
        self.duration = duration
        self.wallet = wallet
        self.scheduledStart = ScheduledStart(**scheduledStart)
        self.marketFilter = MarketFilter(**marketFilter)

class TradeMonitor:
    def __init__(self, settings_path, onSetup, onShutdown):
        self.settings = self.load_settings(settings_path)
        self.onSetup = onSetup
        self.onShutdown = onShutdown

    def setup(self):
        self.onSetup()

    def shutdown(self):
        self.onShutdown()

    def load_settings(self, file_path: str) -> Settings:
        if not os.path.exists(file_path):
            raise ValueError(f"file doesn't exist, {file_path}")

        with open(file_path, "r") as f:
            settings_json = json.load(f)

        settings = Settings(**settings_json)
        return settings

def setting_up(num):
    return num * num

monitor = TradeMonitor("./src/settings.json", setting_up, shutdown)
monitor.setup()
