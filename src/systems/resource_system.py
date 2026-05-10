import time

class ResourceSystem:
    def __init__(self):
        self.players_resources = {1: 150, 2: 150}
        self.last_tick = time.time()
        self.interval = 3.0

    def update(self):
        now = time.time()
        if now - self.last_tick >= self.interval:
            for pid in self.players_resources:
                self.players_resources[pid] += 30
            self.last_tick = now

    def can_afford(self, player_id, cost):
        return self.players_resources[player_id] >= cost

    def spend(self, player_id, cost):
        self.players_resources[player_id] -= cost