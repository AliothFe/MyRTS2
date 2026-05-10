import struct

# 指令类型
CMD_MOVE         = 0x01
CMD_BUILD        = 0x02
CMD_SWITCH_SIEGE = 0x03
CMD_ATTACK       = 0x04
CMD_JOIN         = 0x10
CMD_READY        = 0x11
CMD_START        = 0x12
CMD_ROOM_STATE   = 0x13
CMD_SNAPSHOT     = 0x30

INSTR_LENGTH = {
    CMD_MOVE:          8,
    CMD_BUILD:         3,
    CMD_SWITCH_SIEGE:  5,
    CMD_ATTACK:        6,
    CMD_JOIN:          2,
    CMD_READY:         2,
    CMD_START:         1,
    CMD_ROOM_STATE:    3,
}

SERVER_PORT = 9999

# ---------- 移动 ----------
def pack_move(player_id, unit_id, tx, ty):
    return struct.pack('!BBHHH', CMD_MOVE, player_id, unit_id, int(tx), int(ty))

def unpack_move(data):
    _, pid, uid, tx, ty = struct.unpack('!BBHHH', data)
    return pid, uid, tx, ty

# ---------- 生产 ----------
def pack_build(player_id, unit_type):
    return struct.pack('!BBB', CMD_BUILD, player_id, unit_type)

def unpack_build(data):
    _, pid, utype = struct.unpack('!BBB', data)
    return pid, utype

# ---------- 切换架起 ----------
def pack_switch_siege(player_id, unit_id, mode):
    return struct.pack('!BBHB', CMD_SWITCH_SIEGE, player_id, unit_id, mode)

def unpack_switch_siege(data):
    _, pid, uid, mode = struct.unpack('!BBHB', data)
    return pid, uid, mode

# ---------- 攻击 ----------
def pack_attack(player_id, attacker_id, target_id):
    return struct.pack('!BBHH', CMD_ATTACK, player_id, attacker_id, target_id)

def unpack_attack(data):
    _, pid, aid, tid = struct.unpack('!BBHH', data)
    return pid, aid, tid

# ---------- 房间 ----------
def pack_join(player_id):
    return struct.pack('!BB', CMD_JOIN, player_id)

def pack_ready(player_id):
    return struct.pack('!BB', CMD_READY, player_id)

def pack_start():
    return struct.pack('!B', CMD_START)

def pack_room_state(ready_map):
    return struct.pack('!BBB', CMD_ROOM_STATE,
                       1 if ready_map.get(1, False) else 0,
                       1 if ready_map.get(2, False) else 0)

def unpack_room_state(data):
    _, p1, p2 = struct.unpack('!BBB', data)
    return p1 == 1, p2 == 1

# ---------- 快照（带生产队列） ----------
def pack_snapshot(units, resources, queue_info):
    """
    units: Unit对象列表
    resources: dict {1: p1_res, 2: p2_res}
    queue_info: list of dict [{'player':pid, 'type':'infantry', 'remaining':float_seconds}, ...]
    """
    p1_res = resources.get(1, 0)
    p2_res = resources.get(2, 0)
    num_units = len(units)
    unit_data = b''
    for u in units:
        unit_data += struct.pack('!BBHhhHB',
                             u.owner,
                             u.unit_id,
                             {"infantry":0, "tank":1, "at_infantry":2}[u.type],
                             int(u.x),
                             int(u.y),
                             int(u.hp),                              # 强制转整
                             1 if u.siege_mode else 0)               # 明确转整
    # 队列数据
    queue_data = b''
    for job in queue_info:
        pid = job['player']
        utype = job['type']
        remaining = max(0, int(job['remaining'] * 10))  # 用0.1秒为单位传输，避免浮点
        type_code = {"infantry":0, "tank":1, "at_infantry":2}[utype]
        queue_data += struct.pack('!BBH', pid, type_code, remaining)  # 每项4字节
    num_queue = len(queue_info)
    header = struct.pack('!BHHHH', CMD_SNAPSHOT, p1_res, p2_res, num_units, num_queue)
    return header + unit_data + queue_data

def unpack_snapshot(data):
    """返回 (p1_res, p2_res, units_info, queue_info)"""
    p1_res, p2_res, num_units, num_queue = struct.unpack('!HHHH', data[1:9])
    units_info = []
    offset = 9
    for _ in range(num_units):
        owner, uid, utype_code, x, y, hp, siege = struct.unpack('!BBHhhHB', data[offset:offset+11])
        utype = {0:"infantry", 1:"tank", 2:"at_infantry"}[utype_code]
        units_info.append({
            'owner': owner,
            'id': uid,
            'type': utype,
            'x': x,
            'y': y,
            'hp': hp,
            'siege': siege == 1
        })
        offset += 11
    # 解析队列
    queue_info = []
    for _ in range(num_queue):
        pid, utype_code, remaining_tenths = struct.unpack('!BBH', data[offset:offset+4])
        utype = {0:"infantry", 1:"tank", 2:"at_infantry"}[utype_code]
        remaining = remaining_tenths / 10.0  # 转换回秒
        queue_info.append({'player': pid, 'type': utype, 'remaining': remaining})
        offset += 4
    return p1_res, p2_res, units_info, queue_info