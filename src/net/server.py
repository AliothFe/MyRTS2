import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import socket, time, random
from src.net.protocol import *
from src.core.constants import *
from src.entities.unit import Unit
from src.entities.bullet import Bullet
from src.systems.resource_system import ResourceSystem
from src.systems.production import ProductionSystem
from src.core.config import get_config

SERVER_PORT = 9999
LOGIC_TICK = 1 / FPS
SNAPSHOT_INTERVAL = 0.1

class GameServer:
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('0.0.0.0', SERVER_PORT))
        self.sock.setblocking(False)
        self.clients = {}
        self.ready = {1: False, 2: False}
        # 资源系统内部会从配置读取初始资源等
        self.resource_sys = ResourceSystem()
        self.prod_sys = ProductionSystem()
        self.units = []
        self.bullets = []
        self.next_unit_id = 0
        # 加载全局配置
        self.config = get_config()

    def broadcast(self, data):
        for addr in self.clients:
            self.sock.sendto(data, addr)

    def run(self):
        print("[Server] 启动，等待玩家加入...")
        while len(self.clients) < 2:
            try:
                data, addr = self.sock.recvfrom(1024)
                if data[0] == CMD_JOIN:
                    pid = data[1]
                    if pid in (1,2) and pid not in self.clients.values():
                        self.clients[addr] = pid
                        print(f"玩家{pid}加入")
                        self.broadcast(pack_room_state({1: self.ready[1], 2: self.ready[2]}))
            except BlockingIOError:
                pass
            time.sleep(0.1)

        print("等待准备")
        while not all(self.ready.values()):
            try:
                data, addr = self.sock.recvfrom(1024)
                if data[0] == CMD_READY:
                    pid = data[1]
                    self.ready[pid] = True
                    print(f"玩家{pid}已准备")
                    self.broadcast(pack_room_state({1: self.ready[1], 2: self.ready[2]}))
            except BlockingIOError:
                pass
            time.sleep(0.1)

        print("游戏开始")
        time.sleep(3)
        self.broadcast(pack_start())
        offset_x, offset_y = SCREEN_WIDTH//2, SCREEN_HEIGHT//2
        cfg = self.config
        # 初始单位（用配置中的数据）
        u1 = Unit(offset_x - 30, offset_y - 200, 1, "infantry", self.next_unit_id, cfg["infantry"])
        self.next_unit_id += 1
        u2 = Unit(offset_x + 30, offset_y - 200, 1, "infantry", self.next_unit_id, cfg["infantry"])
        self.next_unit_id += 1
        u3 = Unit(offset_x - 30, offset_y + 200, 2, "infantry", self.next_unit_id, cfg["infantry"])
        self.next_unit_id += 1
        u4 = Unit(offset_x + 30, offset_y + 200, 2, "infantry", self.next_unit_id, cfg["infantry"])
        self.next_unit_id += 1
        self.units = [u1, u2, u3, u4]

        last_logic = time.time()
        last_snapshot = time.time()

        while True:
            now = time.time()
            try:
                while True:
                    data, addr = self.sock.recvfrom(1024)
                    if addr in self.clients:
                        self.handle_instruction(data, self.clients[addr])
            except BlockingIOError:
                pass
            except ConnectionResetError:
                print("客户端断开")
                break

            if now - last_logic >= LOGIC_TICK:
                self.update_world()
                last_logic = now

            if now - last_snapshot >= SNAPSHOT_INTERVAL:
                queue_info = self.prod_sys.get_all_queue_info()
                snapshot = pack_snapshot(self.units, self.resource_sys.players_resources, queue_info)
                self.broadcast(snapshot)
                last_snapshot = now

            time.sleep(0.001)
        self.sock.close()

    def handle_instruction(self, data, player_id):
        cmd = data[0]
        if cmd == CMD_MOVE:
            pid, uid, tx, ty = unpack_move(data)
            u = self._find_unit(uid)
            if u and u.owner == pid:
                u.move_to(tx, ty)
        elif cmd == CMD_BUILD:
            pid, utype_code = unpack_build(data)
            utype = {0:"infantry", 1:"tank", 2:"at_infantry"}[utype_code]
            unit_cfg = self.config[utype]
            cost = unit_cfg['cost']
            if self.resource_sys.can_afford(pid, cost):
                self.resource_sys.spend(pid, cost)
                build_sec = unit_cfg['build_time_sec']
                self.prod_sys.add_to_queue(pid, utype, build_sec)
        elif cmd == CMD_SWITCH_SIEGE:
            pid, uid, mode = unpack_switch_siege(data)
            u = self._find_unit(uid)
            if u and u.owner == pid:
                u.siege_mode = (mode == 1)
        elif cmd == CMD_ATTACK:
            pid, aid, tid = unpack_attack(data)
            attacker = self._find_unit(aid)
            target = self._find_unit(tid)
            if attacker and target and attacker.owner == pid:
                attacker.attack(target, self.bullets, self.units)

    def update_world(self):
        self.resource_sys.update()
        self.next_unit_id = self.prod_sys.update(
            self.units, self.next_unit_id,
            SCREEN_WIDTH//2, SCREEN_HEIGHT//2,
            self.units
        )
        for u in self.units:
            u.update(self.units)
        for b in self.bullets:
            b.update()
        self.bullets = [b for b in self.bullets if b.active]
        self.units = [u for u in self.units if u.hp > 0]

    def _find_unit(self, uid):
        for u in self.units:
            if u.unit_id == uid:
                return u
        return None

if __name__ == "__main__":
    GameServer().run()