import time
from src.core.config import get_config

class ResourceSystem:
    def __init__(self):
        cfg = get_config()['resource']
        self.players_resources = {1: cfg['initial'], 2: cfg['initial']}
        self.last_tick = time.time()
        self.interval = cfg['interval_sec']
        self.per_tick = cfg['per_tick']

    def update(self):
        now = time.time()
        if now - self.last_tick >= self.interval:
            for pid in self.players_resources:
                self.players_resources[pid] += self.per_tick
            self.last_tick = now

    def can_afford(self, player_id, cost):
        return self.players_resources[player_id] >= cost

    def spend(self, player_id, cost):
        self.players_resources[player_id] -= cost