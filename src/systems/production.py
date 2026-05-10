import random, time, math
from src.entities.unit import Unit
from src.core.constants import MAX_PRODUCTION_QUEUE, UNIT_RADIUS

class ProductionSystem:
    def __init__(self):
        self.queue = []  # (pid, unit_type, start_time, duration_sec)

    def add_to_queue(self, pid, unit_type, duration_seconds):
        count = sum(1 for q in self.queue if q[0] == pid)
        if count >= MAX_PRODUCTION_QUEUE:
            return False
        self.queue.append((pid, unit_type, time.time(), duration_seconds))
        return True

    def get_all_queue_info(self):
        """返回所有玩家的队列剩余时间列表"""
        result = []
        for pid, utype, start, dur in self.queue:
            elapsed = time.time() - start
            remaining = max(0.0, dur - elapsed)
            result.append({'player': pid, 'type': utype, 'remaining': remaining})
        return result

    def update(self, units, next_unit_id, offset_x, offset_y, all_units):
        now = time.time()
        finished = []
        for pid, utype, start, dur in self.queue:
            if now - start >= dur:
                # 出生点定位
                if pid == 1:
                    base_x, base_y = offset_x, offset_y - 200
                else:
                    base_x, base_y = offset_x, offset_y + 200
                # 尝试找不重叠的位置
                spawn_x, spawn_y = self._find_free_position(base_x, base_y, all_units, pid)
                unit = Unit(spawn_x, spawn_y, pid, utype, next_unit_id)
                units.append(unit)
                next_unit_id += 1
                finished.append((pid, utype, start, dur))
        for job in finished:
            self.queue.remove(job)
        return next_unit_id

    def _find_free_position(self, cx, cy, all_units, owner):
        """从中心点尝试随机偏移直到不重叠或达到最大尝试次数"""
        for _ in range(30):
            angle = random.uniform(0, math.pi * 2)
            dist = random.uniform(20, 60)
            tx = cx + math.cos(angle) * dist
            ty = cy + math.sin(angle) * dist
            if not self._collides_with_any(tx, ty, all_units, owner):
                return tx, ty
        # 若始终重叠，返回中心（重叠总比卡死好，但很少发生）
        return cx, cy

    def _collides_with_any(self, x, y, units, owner):
        for u in units:
            if u.owner == owner and u.hp > 0:
                if math.hypot(x - u.x, y - u.y) < UNIT_RADIUS * 2:
                    return True
        return False