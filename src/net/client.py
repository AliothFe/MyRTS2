import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import socket, threading, queue, time
from src.net.protocol import *

class NetworkClient:
    def __init__(self, player_id):
        self.player_id = player_id
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('0.0.0.0', 0))
        self.sock.setblocking(False)
        self.server_addr = None
        self.send_queue = queue.Queue()
        self.recv_queue = queue.Queue()
        self.running = True
        self.state = 'menu'
        self.ready_status = False
        self.opponent_ready = False
        self.thread = threading.Thread(target=self._loop, daemon=True)

    def connect_to_server(self, ip):
        self.server_addr = (ip, SERVER_PORT)
        self.send_raw(pack_join(self.player_id))
        self.state = 'room'

    def send_raw(self, data):
        self.send_queue.put(data)

    def send_ready(self):
        self.send_raw(pack_ready(self.player_id))
        self.ready_status = True

    def start(self):
        self.thread.start()

    def stop(self):
        self.running = False
        self.sock.close()

    def send_instruction(self, packed):
        if self.state == 'game':
            self.send_queue.put(packed)

    def get_messages(self):
        """返回所有接收到的消息（快照、开始信号等）"""
        msgs = []
        while not self.recv_queue.empty():
            msgs.append(self.recv_queue.get())
        return msgs

    def _loop(self):
        while self.running:
            while not self.send_queue.empty():
                data = self.send_queue.get()
                if self.server_addr:
                    try:
                        self.sock.sendto(data, self.server_addr)
                    except Exception as e:
                        print("[Client] 发送失败:", e)
            try:
                data, _ = self.sock.recvfrom(4096)
                if data[0] == CMD_SNAPSHOT:
                    self.recv_queue.put(data)
                elif data[0] == CMD_START:
                    self.state = 'game'
                    self.recv_queue.put('start')
                elif data[0] == CMD_ROOM_STATE:
                    p1_ready, p2_ready = unpack_room_state(data)
                    if self.player_id == 1:
                        self.opponent_ready = p2_ready
                    else:
                        self.opponent_ready = p1_ready
            except BlockingIOError:
                pass
            except Exception as e:
                print("[Client] 接收错误:", e)
            time.sleep(0.005)