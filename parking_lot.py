import pygame
from collections import deque
import road
import spot
import heapq
import vehicle

class parkingLot():
    def __init__(self,screen,width,height,shopping):
        self.screen = screen
        self.screen_width = width
        self.screen_height = height
        self.exit = (1350,450)
        self.entrance = (0,450)
        self.nodes = []
        self.spots = {
            "regular": [],
            "cs-near": []
        }
        self.roads = []
        self.vehicles = []
        self.set_grid()
        self.setup_parking_lot()
        
    def setup_parking_lot(self):
        #Roads
        self.roads.append(road.road(self.screen,0,400,'horizontal',1400,100))
        self.grid[8] = [1] * len(self.grid[6])
        self.grid[9] = [1] * len(self.grid[6])
        self.roads.append(road.road(self.screen,100,0,'horizontal',1200,100))
        for i in range(2,len(self.grid[6])-2):
            self.grid[0][i] = 1
            self.grid[1][i] = 1
        self.roads.append(road.road(self.screen,100,700,'horizontal',1200,100))
        for i in range(2,len(self.grid[6])-2):
            self.grid[14][i] = 1
            self.grid[15][i] = 1
        self.roads.append(road.road(self.screen,100,100,'vertical',400,100))
        for i in range(2,9):
            self.grid[i][2] = 1
            self.grid[i][3] = 1
        self.roads.append(road.road(self.screen,100,400,'vertical',400,100))
        for i in range(8,16):
            self.grid[i][2] = 1
            self.grid[i][3] = 1
        self.roads.append(road.road(self.screen,1200,400,'vertical',400,100))
        for i in range(8,16):
            self.grid[i][24] = 1
            self.grid[i][25] = 1
        self.roads.append(road.road(self.screen,1200,100,'vertical',400,100))
        for i in range(2,9):
            self.grid[i][24] = 1
            self.grid[i][25] = 1
        
        # Spots
        for i in range(10):
            self.spots["regular"].append(spot.spot(self.screen,200 + i * 100,300,"regular"))
            self.grid[6][4 + i] = 2
            self.grid[6][23 - i] = 2
            self.grid[7][4 + i] = 2
            self.grid[7][23 - i] = 2
        
        for i in range(6):
            self.spots["regular"].append(spot.spot(self.screen,200 + i * 100,600,"regular"))
            self.grid[12][4 + i] = 2
            self.grid[12][15 - i] = 2
            self.grid[13][4 + i] = 2
            self.grid[13][15 - i] = 2

        for i in range(10):
            self.spots["regular"].append(spot.spot(self.screen,200 + i * 100,100,"regular"))
            self.grid[2][4 + i] = 2
            self.grid[2][23 - i] = 2
            self.grid[3][4 + i] = 2
            self.grid[3][23 - i] = 2

    def set_grid(self):
        grid_size = 50
        self.num_rows = self.screen_height // grid_size
        self.num_cols = self.screen_width // grid_size
        self.grid = [[0 for _ in range(self.num_cols)] for _ in range(self.num_rows)]

    def draw_shopping_center(self, x, y, width=200, height=200):
        # Colors
        self.font = pygame.font.SysFont('Arial', 30, bold=True)
        BUILDING_COLOR = (210, 180, 140)  # Light brown
        DOOR_COLOR = (101, 67, 33)        # Dark brown
        WINDOW_COLOR = (135, 206, 235)    # Glassy blue
        WINDOW_FRAME = (80, 50, 20)       # Dark frame
        SIGN_COLOR = (220, 20, 60)        # Red-ish
        SIGN_TEXT_COLOR = (255, 255, 255)# White

        # Draw building
        pygame.draw.rect(self.screen, BUILDING_COLOR, (x, y, width, height), border_radius=10)

        # Draw smaller door
        door_width = width // 6
        door_height = height // 3
        door_x = x + width // 2 - door_width // 2
        door_y = y + height - door_height
        pygame.draw.rect(self.screen, DOOR_COLOR, (door_x, door_y, door_width, door_height), border_radius=5)

        # Draw windows (two rows)
        num_windows = 3
        window_width = width // 5
        window_height = height // 6
        window_gap = (width - num_windows * window_width) // (num_windows + 1)

        # First row
        for i in range(num_windows):
            window_x = x + window_gap + i * (window_width + window_gap)
            window_y = y + window_height * 3
            pygame.draw.rect(self.screen, WINDOW_FRAME, (window_x-2, window_y-2, window_width+4, window_height+4), border_radius=3)
            pygame.draw.rect(self.screen, WINDOW_COLOR, (window_x, window_y, window_width, window_height), border_radius=3)

        # Second row
        for i in range(num_windows):
            window_x = x + window_gap + i * (window_width + window_gap)
            window_y = y + window_height * 1.5
            pygame.draw.rect(self.screen, WINDOW_FRAME, (window_x-2, window_y-2, window_width+4, window_height+4), border_radius=3)
            pygame.draw.rect(self.screen, WINDOW_COLOR, (window_x, window_y, window_width, window_height), border_radius=3)

        # Draw sign above door
        sign_width = width // 2
        sign_height = 40
        sign_x = x + (width - sign_width) // 2
        sign_y = y
        pygame.draw.rect(self.screen, SIGN_COLOR, (sign_x, sign_y, sign_width, sign_height), border_radius=5)

        # Sign text
        sign_text = self.font.render('Mall', True, SIGN_TEXT_COLOR)
        text_x = sign_x + (sign_width - sign_text.get_width()) // 2
        text_y = sign_y + (sign_height - sign_text.get_height()) // 2
        self.screen.blit(sign_text, (text_x, text_y))


    def update(self):
        for v in self.vehicles:
            v.update()
            if v.target_index >= len(v.path):
                if v.state == "parking":
                    v.state = "parked"
                    v.park_timer = v.park_duration

                elif v.state == "parked":
                    v.park_timer -= 1
                    if v.park_timer <= 0:
                        v.state = "to_exit"
                        
                        grid_size = 50
                        spot_row = int(v.y // grid_size)
                        spot_col = int(v.x // grid_size)
                        
                        if spot_row <= 3:
                            road_row = 1
                        elif 6 <= spot_row <= 7:
                            road_row = 8
                        else:
                            road_row = 14
                        
                        road_start_pixel = (spot_col * grid_size + 25, road_row * grid_size + 25)
                        
                        new_path = self.find_path(road_start_pixel, self.exit)
                        
                        if new_path:
                            centered_path = []
                            
                            centered_path.append((v.x, road_row * 50 + 25))
                            
                            for row, col in new_path:
                                pixel_x = (col // 2) * 100 + 50
                                pixel_y = (row // 2) * 100 + 50
                                centered_path.append((pixel_x, pixel_y))
                            
                            v.set_path(centered_path)
                        
                        v.target.occupied = False
                        
                elif v.state == "to_exit":
                    self.remove_vehicle(v.id)


    def display_grid(self):
        grid_size = 50
        color_map = {0: (255, 255, 0), 2: (0, 0, 255)}
        default_color = (255, 0, 0)
        for row in range(self.num_rows):
            for col in range(self.num_cols):
                try:
                    cell = self.grid[row][col]
                except Exception:
                    cell = 0
                color = color_map.get(cell, default_color)
                rect = pygame.Rect(col * grid_size, row * grid_size, grid_size, grid_size)
                pygame.draw.rect(self.screen, color, rect)
                pygame.draw.rect(self.screen, (200, 200, 200), rect, 1)


    def draw_sign(self,x,y,size,color,text_color,text):
        pygame.draw.line(self.screen, color, (x + 20, y+size/2), (x + 20, y + size/2 + 30), 4)
        pygame.draw.line(self.screen, color, (x+size - 25, y+size/2), (x + size - 25, y + size/2 + 30), 4)
        pygame.draw.rect(self.screen, color, (x,y, size, size/2))
        font = pygame.font.Font(None, 20)
        text_surface = font.render(text, True, text_color)
        text_rect = text_surface.get_rect(center=(x + size/2, y + (size/2)/2))

        self.screen.blit(text_surface, text_rect)

    def draw_parking_lot(self):
        for road in self.roads:
            road.draw_road()
        for spot_list in self.spots.values():
            for s in spot_list:
                s.draw_spot()
        for vehicle in self.vehicles:
            vehicle.draw_vehicle()

        self.draw_sign(12.5,325,80,(0,0,0),(0,255,0),'Entrance')
        self.draw_sign(1312.5,325,80,(0,0,0),(255,0,0),'Exit')
        self.draw_shopping_center(900,500)

    def assign_spot(self,vehicle):
        if not vehicle.is_ev:
            for s in self.spots["regular"]:
                if not s.occupied:
                    vehicle.target = s
                    s.occupied = True
                    return 1
        return -1

    def heuristic(self, a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def add_vehicle(self, car):
        car.is_ev = False
        new_veh = vehicle.vehicle(self.screen, car.id, car.is_ev, 2.5, "parking", self.entrance, car.park_duration)
        
        if self.assign_spot(new_veh) != -1:
            self.vehicles.append(new_veh)
            
            grid_size = 50
            spot_x = new_veh.target.middle_x
            spot_y = new_veh.target.middle_y
            
            spot_row = int(spot_y // grid_size)
            spot_col = int(spot_x // grid_size)
            
            if spot_row <= 3:
                road_row = 1
            elif 6 <= spot_row <= 7:
                road_row = 8
            else:
                road_row = 14
            
            road_target_pixel = (spot_col * grid_size + 25, road_row * grid_size + 25)
            
            raw_path = self.find_path((new_veh.x, new_veh.y), road_target_pixel)
            
            if not raw_path:
                return
            
            path_pixels = []
            for row, col in raw_path:
                pixel_x = (col // 2) * 100 + 50
                pixel_y = (row // 2) * 100 + 50
                path_pixels.append((pixel_x, pixel_y))
            
            path_pixels.append((spot_x, spot_y))
            
            new_veh.set_path(path_pixels)

    def remove_vehicle(self, id):
        to_remove = None
        for vehicle in self.vehicles:
            if vehicle.id == id:
                to_remove = vehicle
        
        self.vehicles.remove(to_remove)
                


    def find_path(self, start_pixel, end_pixel):
        grid_size = 50
        start_node = (int(start_pixel[1] // grid_size), int(start_pixel[0] // grid_size))
        end_node = (int(end_pixel[1] // grid_size), int(end_pixel[0] // grid_size))

        open_set = []
        heapq.heappush(open_set, (0, start_node, 0))
        came_from = {start_node: None}
        cost_so_far = {start_node: 0}
        path_found = False

        while open_set:
            _, current, last_dir = heapq.heappop(open_set)
            if current == end_node:
                path_found = True
                break

            for dr, dc, move_dir in [(current[0]-1, current[1], 1), (current[0]+1, current[1], 2), 
                                     (current[0], current[1]-1, 3), (current[0], current[1]+1, 4)]:
                if 0 <= dr < self.num_rows and 0 <= dc < self.num_cols:
                    # ONLY drive on roads (1) for navigation
                    if self.grid[dr][dc] == 1 or (dr, dc) == end_node:
                        move_cost = 1
                        if last_dir != 0 and move_dir != last_dir:
                            move_cost += 20 # Severe penalty for turning
                        
                        new_cost = cost_so_far[current] + move_cost
                        if (dr, dc) not in cost_so_far or new_cost < cost_so_far[(dr, dc)]:
                            cost_so_far[(dr, dc)] = new_cost
                            priority = new_cost + self.heuristic((dr, dc), end_node)
                            heapq.heappush(open_set, (priority, (dr, dc), move_dir))
                            came_from[(dr, dc)] = current

        path = []
        if path_found:
            curr = end_node
            while curr is not None:
                path.append(curr)
                curr = came_from[curr]
            path.reverse()
        return path