import pygame
import math
from src.core.constants import *

class Unit:
    def __init__(self, x, y, owner, unit_type, unit_id):
        self.x = x
        self.y = y
        self.owner = owner  # 1 或 2
        self.type = unit_type
        self.unit_id = unit_id

        if unit_type == "infantry":
            self.max_hp = INFANTRY_HP
            self.speed = INFANTRY_SPEED
            self.range = INFANTRY_RANGE
            self.damage = INFANTRY_DAMAGE
            self.attack_cooldown = INFANTRY_ATTACK_COOLDOWN
            self.cost = INFANTRY_COST
            self.build_time = INFANTRY_BUILD_TIME
        elif unit_type == "tank":
            self.max_hp = TANK_HP
            self.speed = TANK_SPEED
            self.range = TANK_RANGE
            self.damage = TANK_DAMAGE
            self.attack_cooldown = TANK_ATTACK_COOLDOWN
            self.cost = TANK_COST
            self.build_time = TANK_BUILD_TIME
        elif unit_type == "at_infantry":
            self.max_hp = AT_INFANTRY_HP
            self.speed = AT_INFANTRY_SPEED
            self.range = AT_INFANTRY_RANGE
            self.damage = AT_INFANTRY_DAMAGE_VS_INFANTRY
            self.attack_cooldown = AT_INFANTRY_ATTACK_COOLDOWN
            self.cost = AT_INFANTRY_COST
            self.build_time = AT_INFANTRY_BUILD_TIME
        else:
            raise ValueError(f"Unknown unit type {unit_type}")

        self.hp = self.max_hp
        self.attack_timer = 0
        self.target_pos = None
        self.selected = False
        self.siege_mode = False
        self.can_siege = (unit_type == "tank")
        self.radius = UNIT_RADIUS

    def update(self, units):
        if self.attack_timer > 0:
            self.attack_timer -= 1

        # 移动（架起模式禁止）
        if self.target_pos is not None and not self.siege_mode:
            dx = self.target_pos[0] - self.x
            dy = self.target_pos[1] - self.y
            dist = math.hypot(dx, dy)
            if dist < self.speed:
                self.x, self.y = self.target_pos
                self.target_pos = None
            else:
                nx = self.x + dx / dist * self.speed
                ny = self.y + dy / dist * self.speed
                if not self._collides_with_any(nx, ny, units):
                    self.x, self.y = nx, ny
                else:
                    self.target_pos = None

    def attack(self, target, bullets, all_units):
        if self.attack_timer > 0 or self.hp <= 0 or target.hp <= 0:
            return False
        if math.hypot(self.x - target.x, self.y - target.y) > self.range:
            return False
        self.attack_timer = self.attack_cooldown
        self._fire_upon(target, bullets, all_units)
        return True

    def _fire_upon(self, target, bullets, all_units):
        if self.type == "tank" and not self.siege_mode:
            from src.entities.bullet import Bullet
            bullet = Bullet(self.x, self.y, target, self.damage, self.owner)
            bullets.append(bullet)
        elif self.type == "tank" and self.siege_mode:
            target.take_damage(self.damage)
            for u in self._get_nearby_units(target, all_units):
                if u.owner != self.owner and u.hp > 0:
                    u.take_damage(self.damage * 0.5)
        else:
            if self.type == "at_infantry":
                dmg = AT_INFANTRY_DAMAGE_VS_TANK if target.type == "tank" else AT_INFANTRY_DAMAGE_VS_INFANTRY
            else:
                dmg = self.damage
            target.take_damage(dmg)

    def take_damage(self, dmg):
        if self.siege_mode and self.type == "tank":
            dmg *= (1 - TANK_SIEGE_DMG_REDUCTION)
        self.hp -= dmg
        if self.hp <= 0:
            self.hp = 0

    def move_to(self, tx, ty):
        self.target_pos = (tx, ty)

    def contains_point(self, px, py):
        return (self.x - px)**2 + (self.y - py)**2 <= self.radius**2

    def _collides_with_any(self, nx, ny, units):
        for other in units:
            if other is self or other.hp <= 0:
                continue
            if math.hypot(nx - other.x, ny - other.y) < self.radius + other.radius:
                return True
        return False

    def _get_nearby_units(self, target, units, radius=50):
        ret = []
        for u in units:
            if u is target or u.hp <= 0:
                continue
            if math.hypot(target.x - u.x, target.y - u.y) <= radius:
                ret.append(u)
        return ret

    def draw(self, screen):
        if self.hp <= 0:
            return
        if self.owner == 1:
            if self.type == "infantry":   color = (50, 150, 255)
            elif self.type == "tank":     color = (30, 80, 200)
            elif self.type == "at_infantry": color = (100, 100, 255)
        else:
            if self.type == "infantry":   color = (255, 120, 120)
            elif self.type == "tank":     color = (200, 50, 50)
            elif self.type == "at_infantry": color = (255, 80, 180)

        if self.type == "tank":
            rect = pygame.Rect(0, 0, 22, 22)
            rect.center = (int(self.x), int(self.y))
            pygame.draw.rect(screen, color, rect)
        elif self.type == "infantry":
            pygame.draw.circle(screen, color, (int(self.x), int(self.y)), 10)
        elif self.type == "at_infantry":
            points = [(self.x, self.y-10), (self.x-7, self.y),
                      (self.x, self.y+10), (self.x+7, self.y)]
            pygame.draw.polygon(screen, color, points)

        if self.can_siege and self.siege_mode:
            pygame.draw.circle(screen, COLOR_YELLOW, (int(self.x), int(self.y)), 12, 2)
        if self.selected:
            pygame.draw.circle(screen, COLOR_WHITE, (int(self.x), int(self.y)), 14, 2)

        if self.hp > 0:
            bar_w, bar_h = 24, 4
            bx = self.x - bar_w/2
            by = self.y - 18
            pygame.draw.rect(screen, (60, 60, 60), (bx, by, bar_w, bar_h))
            pygame.draw.rect(screen, COLOR_GREEN,
                             (bx, by, bar_w * (self.hp / self.max_hp), bar_h))