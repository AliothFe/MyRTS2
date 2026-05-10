import pygame
from src.core.constants import *

class GameUI:
    def __init__(self, screen):
        self.screen = screen
        try:
            self.font = pygame.font.Font("C:/Windows/Fonts/simhei.ttf", 20)
        except:
            try:
                self.font = pygame.font.Font("C:/Windows/Fonts/msyh.ttf", 20)
            except:
                self.font = pygame.font.Font(None, 20)
        self.small_font = pygame.font.Font(None, 16)

    def draw(self, resources, player_id, control_groups=None,
             production_queue=None, frame_count=0, pressed_keys=None):
        if pressed_keys is None:
            pressed_keys = {}
        # 面板背景
        panel_rect = pygame.Rect(0, 0, 220, SCREEN_HEIGHT)
        pygame.draw.rect(self.screen, UI_BG_COLOR, panel_rect)
        pygame.draw.rect(self.screen, UI_BORDER_COLOR, panel_rect, 2)

        # 资源
        res = resources.get(player_id, 0)
        res_text = self.font.render(f"矿: {res}", True, COLOR_WHITE)
        self.screen.blit(res_text, (10, 10))

        # 快捷键提示
        tips = [
            ("Q", "步兵 (60)"),
            ("W", "坦克 (180)"),
            ("E", "反坦克步兵 (80)"),
            ("F", "坦克架起"),
            ("A+右键", "攻击"),
            ("Ctrl+数字", "编队")
        ]
        y = 40
        for key, desc in tips:
            key_pressed = pressed_keys.get(key, 0) > 0
            bg_color = UI_KEY_PRESSED_COLOR if key_pressed else None
            txt_col = COLOR_BLACK if key_pressed else COLOR_WHITE
            key_rect = pygame.Rect(10, y, 30, 20)
            if bg_color:
                pygame.draw.rect(self.screen, bg_color, key_rect)
                pygame.draw.rect(self.screen, COLOR_BLACK, key_rect, 1)
            key_surf = self.font.render(key, True, txt_col)
            self.screen.blit(key_surf, (15, y))
            desc_surf = self.font.render(desc, True, COLOR_WHITE)
            self.screen.blit(desc_surf, (50, y))
            y += 25

        # 生产进度
        if production_queue:
            y += 5
            title = self.font.render("生产中", True, COLOR_YELLOW)
            self.screen.blit(title, (10, y))
            y += 25
            for utype, start, dur in production_queue:
                progress = min(1.0, (frame_count - start) / dur) if dur > 0 else 1.0
                bar_w, bar_h = 180, 16
                bar_x, bar_y = 10, y
                pygame.draw.rect(self.screen, COLOR_GREY, (bar_x, bar_y, bar_w, bar_h))
                fill_w = int(bar_w * progress)
                if fill_w > 0:
                    pygame.draw.rect(self.screen, COLOR_GREEN, (bar_x, bar_y, fill_w, bar_h))
                pygame.draw.rect(self.screen, COLOR_WHITE, (bar_x, bar_y, bar_w, bar_h), 1)
                type_surf = self.small_font.render(utype, True, COLOR_WHITE)
                self.screen.blit(type_surf, (bar_x + 5, bar_y + 1))
                remaining = max(0, dur - (frame_count - start))
                time_text = self.small_font.render(f"{remaining / FPS:.1f}s", True, COLOR_WHITE)
                self.screen.blit(time_text, (bar_x + bar_w - 50, bar_y + 1))
                y += 22

        # 编队信息
        if control_groups:
            sep_y = SCREEN_HEIGHT - 130
            pygame.draw.line(self.screen, UI_BORDER_COLOR, (10, sep_y), (210, sep_y), 1)
            y = sep_y + 10
            for grp_key, ids in control_groups.items():
                if not ids:
                    continue
                key_pressed = pressed_keys.get(grp_key, 0) > 0
                bg = UI_KEY_PRESSED_COLOR if key_pressed else None
                txt_col = COLOR_BLACK if key_pressed else COLOR_YELLOW
                grp_rect = pygame.Rect(10, y, 30, 20)
                if bg:
                    pygame.draw.rect(self.screen, bg, grp_rect)
                    pygame.draw.rect(self.screen, COLOR_BLACK, grp_rect, 1)
                key_s = self.font.render(grp_key, True, txt_col)
                self.screen.blit(key_s, (15, y))
                info = f"编队 {grp_key}: {len(ids)} 人"
                info_s = self.font.render(info, True, COLOR_WHITE)
                self.screen.blit(info_s, (50, y))
                y += 22

    def draw_room(self, state, my_ready, opponent_ready):
        self.screen.fill(COLOR_BLACK)
        title = self.font.render("对战房间", True, COLOR_WHITE)
        self.screen.blit(title, (SCREEN_WIDTH//2 - 40, 150))
        my_status = "已准备" if my_ready else "未准备 (按R准备)"
        opp_status = "已准备" if opponent_ready else "等待对方准备..."
        color_my = COLOR_GREEN if my_ready else COLOR_YELLOW
        color_opp = COLOR_GREEN if opponent_ready else COLOR_RED
        text1 = self.font.render(f"你的状态: {my_status}", True, color_my)
        self.screen.blit(text1, (SCREEN_WIDTH//2 - 80, 200))
        text2 = self.font.render(f"对方状态: {opp_status}", True, color_opp)
        self.screen.blit(text2, (SCREEN_WIDTH//2 - 80, 240))
        hint = "等待两人都准备..." if state == 'wait_start' else "即将开始！"
        if hint:
            hint_surf = self.font.render(hint, True, COLOR_GREY)
            self.screen.blit(hint_surf, (SCREEN_WIDTH//2 - 60, 290))

    def draw_menu(self, input_ip="", message=""):
        self.screen.fill(COLOR_BLACK)
        title = self.font.render("My RTS v1.0", True, COLOR_WHITE)
        self.screen.blit(title, (SCREEN_WIDTH//2 - 60, 200))
        ip_label = self.font.render("服务器IP:", True, COLOR_WHITE)
        self.screen.blit(ip_label, (SCREEN_WIDTH//2 - 100, 260))
        ip_text = self.font.render(input_ip, True, COLOR_YELLOW)
        self.screen.blit(ip_text, (SCREEN_WIDTH//2, 260))
        hint = self.font.render("输入IP后按回车连接", True, COLOR_GREY)
        self.screen.blit(hint, (SCREEN_WIDTH//2 - 70, 290))
        if message:
            msg_surf = self.font.render(message, True, COLOR_RED)
            self.screen.blit(msg_surf, (SCREEN_WIDTH//2 - 60, 320))