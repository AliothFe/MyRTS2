import pygame
import math

class Bullet:
    def __init__(self, x, y, target, damage, owner):
        self.x = x
        self.y = y
        self.target = target
        self.damage = damage
        self.owner = owner
        self.speed = 8
        self.active = True

    def update(self):
        if self.target is None or self.target.hp <= 0:
            self.active = False
            return
        dx = self.target.x - self.x
        dy = self.target.y - self.y
        dist = math.hypot(dx, dy)
        if dist < self.speed:
            self.target.take_damage(self.damage)
            self.active = False
        else:
            self.x += dx / dist * self.speed
            self.y += dy / dist * self.speed

    def draw(self, screen):
        pygame.draw.circle(screen, (255, 255, 0), (int(self.x), int(self.y)), 3)