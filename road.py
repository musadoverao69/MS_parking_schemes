import pygame

class road():
    def __init__(self,screen,x,y,roadtype,length,width):
        self.screen = screen
        self.length = length
        self.width = width
        self.roadtype = roadtype
        self.x = x
        self.y = y

    def draw_road(self):
        if self.roadtype == 'vertical':
            pygame.draw.rect(self.screen, (50, 50, 50), (self.x, self.y, self.width, self.length))
            self.draw_road_lines()

        elif self.roadtype == 'horizontal':
            pygame.draw.rect(self.screen, (50, 50, 50), (self.x, self.y, self.length, self.width))
            self.draw_road_lines()

    
    def draw_road_lines(self):
        if self.roadtype == 'vertical':
            gap = 80
            for i in range(self.length // gap):
                pygame.draw.line(self.screen, (255, 255, 0), (self.x + self.width/2, self.y + i * gap + 20), (self.x + self.width/2, self.y + i * gap + 40), 5)
            return
        elif self.roadtype == 'horizontal':
            gap = 80
            for i in range(self.length // gap):
                pygame.draw.line(self.screen, (255, 255, 0), (self.x + i * gap + 20, self.y + self.width/2), (self.x + i * gap + 40, self.y + self.width/2), 5)