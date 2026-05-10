import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import argparse, math, pygame
from src.core.constants import *
from src.core.game_map import create_hex_map, get_base_positions
from src.core.hex_utils import axial_to_pixel, get_hex_corners
from src.ui.game_ui import GameUI
from src.net.client import NetworkClient
from src.net.protocol import *

def _draw_unit_from_info(info, screen, my_id):
    x, y = info['x'], info['y']
    owner = info['owner']
    utype = info['type']
    hp = info['hp']
    siege = info.get('siege', False)
    selected = info.get('selected', False)

    if owner == 1:
        if utype == "infantry":   color = (50, 150, 255)
        elif utype == "tank":     color = (30, 80, 200)
        elif utype == "at_infantry": color = (100, 100, 255)
    else:
        if utype == "infantry":   color = (255, 120, 120)
        elif utype == "tank":     color = (200, 50, 50)
        elif utype == "at_infantry": color = (255, 80, 180)

    if utype == "tank":
        rect = pygame.Rect(0, 0, 22, 22)
        rect.center = (int(x), int(y))
        pygame.draw.rect(screen, color, rect)
    elif utype == "infantry":
        pygame.draw.circle(screen, color, (int(x), int(y)), 10)
    elif utype == "at_infantry":
        points = [(x, y-10), (x-7, y), (x, y+10), (x+7, y)]
        pygame.draw.polygon(screen, color, points)

    if siege:
        pygame.draw.circle(screen, COLOR_YELLOW, (int(x), int(y)), 12, 2)
    if selected:
        pygame.draw.circle(screen, COLOR_WHITE, (int(x), int(y)), 14, 2)

    if hp > 0:
        bar_w, bar_h = 24, 4
        bx = x - bar_w/2
        by = y - 18
        max_hp = {"infantry":INFANTRY_HP, "tank":TANK_HP, "at_infantry":AT_INFANTRY_HP}[utype]
        pygame.draw.rect(screen, (60, 60, 60), (bx, by, bar_w, bar_h))
        pygame.draw.rect(screen, COLOR_GREEN, (bx, by, bar_w * (hp / max_hp), bar_h))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--player', type=int, default=1)
    args = parser.parse_args()
    my_id = args.player

    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("My RTS v1.0")
    clock = pygame.time.Clock()
    ui = GameUI(screen)

    network = NetworkClient(my_id)
    network.start()

    state = 'menu'
    input_ip = "127.0.0.1"
    message = ""
    game_started = False

    units_info = []
    resources = {1: 150, 2: 150}
    selected_ids = set()
    control_groups = {str(k): [] for k in range(1, 10)}
    attack_mode = False
    pressed_feedback = {}
    key_down_held = {}
    selecting = False
    select_start = (0, 0)
    client_frame = 0
    queue_display = []

    hex_map = create_hex_map()
    top_base, bottom_base = get_base_positions()
    offset_x, offset_y = SCREEN_WIDTH//2, SCREEN_HEIGHT//2

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if state == 'menu':
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        if input_ip:
                            network.connect_to_server(input_ip)
                            state = 'room'
                            message = ""
                        else:
                            message = "请输入IP"
                    elif event.key == pygame.K_BACKSPACE:
                        input_ip = input_ip[:-1]
                    else:
                        input_ip += event.unicode

            elif state == 'room':
                if event.type == pygame.KEYUP and event.key == pygame.K_r:
                    network.send_ready()

            elif state == 'game':
                if event.type == pygame.KEYDOWN:
                    if event.key in key_down_held and key_down_held[event.key]:
                        continue
                    key_down_held[event.key] = True

                    if event.key == pygame.K_a:
                        attack_mode = True
                    elif event.key in range(pygame.K_1, pygame.K_9 + 1):
                        key = chr(event.key)
                        mods = pygame.key.get_mods()
                        if mods & pygame.KMOD_CTRL:
                            control_groups[key] = list(selected_ids)
                            pressed_feedback[key] = 10
                        else:
                            selected_ids = set(control_groups.get(key, []))
                            pressed_feedback[key] = 10
                    elif event.key == pygame.K_q:
                        network.send_instruction(pack_build(my_id, 0))
                        pressed_feedback['Q'] = 10
                    elif event.key == pygame.K_w:
                        network.send_instruction(pack_build(my_id, 1))
                        pressed_feedback['W'] = 10
                    elif event.key == pygame.K_e:
                        network.send_instruction(pack_build(my_id, 2))
                        pressed_feedback['E'] = 10
                    elif event.key == pygame.K_f:
                        for uid in list(selected_ids):
                            cu = next((u for u in units_info if u['id'] == uid), None)
                            if cu and cu['owner'] == my_id and cu['type'] == 'tank':
                                mode = 0 if cu['siege'] else 1
                                network.send_instruction(pack_switch_siege(my_id, uid, mode))
                        pressed_feedback['F'] = 10
                elif event.type == pygame.KEYUP:
                    key_down_held[event.key] = False
                    if event.key == pygame.K_a:
                        attack_mode = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        selecting = True
                        select_start = pygame.mouse.get_pos()
                    elif event.button == 3:
                        mx, my = pygame.mouse.get_pos()
                        if attack_mode:
                            for u in units_info:
                                if u['owner'] != my_id and math.hypot(u['x']-mx, u['y']-my) < 15:
                                    target_id = u['id']
                                    for suid in list(selected_ids):
                                        network.send_instruction(pack_attack(my_id, suid, target_id))
                                    break
                        else:
                            if selected_ids:
                                n = len(selected_ids)
                                angle_step = 2 * math.pi / n
                                i = 0
                                for uid in list(selected_ids):
                                    tx = int(mx + 30 * math.cos(i * angle_step)) if n > 1 else mx
                                    ty = int(my + 30 * math.sin(i * angle_step)) if n > 1 else my
                                    network.send_instruction(pack_move(my_id, uid, tx, ty))
                                    i += 1
                elif event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1 and selecting:
                        selecting = False
                        end = pygame.mouse.get_pos()
                        rect = pygame.Rect(
                            min(select_start[0], end[0]),
                            min(select_start[1], end[1]),
                            abs(select_start[0] - end[0]),
                            abs(select_start[1] - end[1])
                        )
                        selected_ids.clear()
                        for u in units_info:
                            if u['owner'] == my_id and rect.collidepoint(u['x'], u['y']):
                                selected_ids.add(u['id'])

        # 接收服务器消息
        msgs = network.get_messages()
        for msg in msgs:
            if msg == 'start':
                state = 'game'
                game_started = True
            elif isinstance(msg, bytes) and msg[0] == CMD_SNAPSHOT:
                p1_res, p2_res, new_units, queue_info = unpack_snapshot(msg)
                resources = {1: p1_res, 2: p2_res}
                units_info = new_units
                valid_ids = {u['id'] for u in units_info}
                selected_ids &= valid_ids

                # 构造进度条显示数据
                queue_display = []
                for q in queue_info:
                    total_sec = {"infantry":8, "tank":16, "at_infantry":8}[q['type']]
                    remaining_sec = q['remaining']
                    total_frames = total_sec * FPS
                    remaining_frames = remaining_sec * FPS
                    start_frame = client_frame - (total_frames - remaining_frames)
                    queue_display.append((q['type'], start_frame, total_frames))

        # 按键反馈衰减
        for k in list(pressed_feedback.keys()):
            pressed_feedback[k] -= 1
            if pressed_feedback[k] <= 0:
                del pressed_feedback[k]

        # 渲染
        screen.fill(COLOR_BLACK)

        if state == 'menu':
            ui.draw_menu(input_ip, message)
        elif state == 'room':
            ui.draw_room('wait_start', network.ready_status, network.opponent_ready)
        elif state == 'game' and game_started:
            # 地图
            for q, r in hex_map:
                x, y = axial_to_pixel(q, r)
                cx, cy = x + offset_x, y + offset_y
                corners = get_hex_corners(cx, cy)
                pygame.draw.polygon(screen, COLOR_GREY, corners, 2)
            for base_pos, oid in [(top_base, 1), (bottom_base, 2)]:
                x, y = axial_to_pixel(*base_pos)
                cx, cy = x + offset_x, y + offset_y
                color = COLOR_BLUE if oid == my_id else COLOR_RED
                pygame.draw.polygon(screen, color, get_hex_corners(cx, cy))

            # ========== 战争迷雾：只绘制可见单位 ==========
            my_units = [u for u in units_info if u['owner'] == my_id]
            sight_range = 150
            visible_ids = set()
            for mu in my_units:
                for u in units_info:
                    if math.hypot(mu['x'] - u['x'], mu['y'] - u['y']) <= sight_range:
                        visible_ids.add(u['id'])
            for u in units_info:
                if u['id'] in visible_ids or u['owner'] == my_id:
                    u['selected'] = (u['id'] in selected_ids)
                    _draw_unit_from_info(u, screen, my_id)

            # UI（包含进度条）
            ui.draw(resources, my_id, control_groups,
                    production_queue=queue_display,
                    frame_count=client_frame,
                    pressed_keys=pressed_feedback)

            if selecting:
                mx, my = pygame.mouse.get_pos()
                rect = pygame.Rect(
                    min(select_start[0], mx), min(select_start[1], my),
                    abs(select_start[0] - mx), abs(select_start[1] - my)
                )
                pygame.draw.rect(screen, COLOR_GREEN, rect, 2)

        client_frame += 1
        pygame.display.flip()
        clock.tick(FPS)

    network.stop()
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()