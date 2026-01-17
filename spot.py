import pygame
class spot:
    def __init__(self,screen,x,y,type,occupied=False):
        self.screen = screen
        self.x = x
        self.y = y
        self.type = type
        self.middle_x = x + 50
        self.middle_y = y + 50
        self.occupied = occupied
        self.width = 100
        self.height = 100

    def draw_spot(self):
        if self.type == "ev":
            color = (0, 255, 0)
        else:
            color = (0, 0, 0)
        pygame.draw.rect(self.screen, color, (self.x, self.y, self.height, self.width), 2)