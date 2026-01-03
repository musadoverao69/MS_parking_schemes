import pygame
import math
class vehicle:
    def __init__(self, screen, id , is_ev, speed,state, position, park_duration=0):
        self.id = id
        self.screen = screen
        self.is_ev = is_ev
        self.speed = speed * 3
        self.state = state
        self.timer = 0.0
        self.position = position
        self.x = position[0]
        self.y = position[1]
        self.width = 28
        self.height = 18
        self.spot = None
        self.angle = 0 
        self.park_duration = park_duration

    def set_path(self,path):
        self.path = path
        self.target_index = 0

    def draw_vehicle(self):
        surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)

        body_color = (255, 40, 0) 
        pygame.draw.rect(surf, body_color, (0, self.height * 0.2, self.width, self.height * 0.6), border_radius=6)

        pygame.draw.rect(surf, (150, 0, 0), (self.width * 0.25, 0, self.width * 0.5, self.height * 0.4), border_radius=4)

        wheel_color = (30, 30, 30)
        wheel_radius = int(self.height * 0.2)
        pygame.draw.circle(surf, wheel_color, (int(self.width * 0.2), int(self.height * 0.85)), wheel_radius)
        pygame.draw.circle(surf, wheel_color, (int(self.width * 0.8), int(self.height * 0.85)), wheel_radius)

        rotated = pygame.transform.rotate(surf, self.angle)
        rect = rotated.get_rect(center=(self.x, self.y))

        self.screen.blit(rotated, rect)


    def update(self):
        if not self.path or self.target_index >= len(self.path):
            return

        tx, ty = self.path[self.target_index]

        dx = tx - self.x
        dy = ty - self.y
        dist = math.hypot(dx, dy)

        if dist > 0:
            self.angle = math.degrees(math.atan2(-dy, dx))

        # Snap to point
        if dist < self.speed:
            self.x = tx
            self.y = ty
            self.target_index += 1
            return

        # Move toward target
        self.x += (dx / dist) * self.speed
        self.y += (dy / dist) * self.speed


    