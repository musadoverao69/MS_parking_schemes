"""
Visualizador Pygame para Parking Lot Simulation

Visualização com vista lateral:
- Carros entram pela esquerda
- Estrada horizontal no centro
- Vagas perpendiculares acima e abaixo da estrada
- Carros viram 90° para estacionar
"""
import pygame
import math
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import queue
import threading
import time


# Cores
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)
DARK_GRAY = (64, 64, 64)
LIGHT_GRAY = (200, 200, 200)
GREEN = (0, 255, 0)
DARK_GREEN = (0, 200, 0)
BLUE = (100, 150, 255)
DARK_BLUE = (50, 100, 200)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)
LIGHT_BLUE = (173, 216, 230)
PARKING_GRAY = (40, 40, 40)


class VehicleState(Enum):
    """Estados do veículo"""
    ARRIVING = "arriving"
    WAITING = "waiting"
    PARKED = "parked"
    DEPARTING = "departing"


@dataclass
class VehicleVisual:
    """Dados visuais de um veículo"""
    id: str
    is_ev: bool
    x: float
    y: float
    state: VehicleState
    spot_name: Optional[str] = None
    battery_level: Optional[str] = None
    target_x: float = 0
    target_y: float = 0
    speed: float = 2.0
    angle: float = 0


class ParkingLotVisualizerPygame:
    """Visualizador do parking lot usando Pygame - Vista lateral"""
    
    def __init__(self, parking_lot, config):
        self.parking_lot = parking_lot
        self.config = config
        
        # Queue para comunicação com SimPy
        self.event_queue = queue.Queue()
        self.running = True
        
        # Dados de visualização
        self.vehicles: Dict[str, VehicleVisual] = {}
        
        # Rastreamento de vagas ocupadas
        self.occupied_regular_spots: Dict[tuple, str] = {}
        self.occupied_cs_spots: Dict[tuple, str] = {}
        
        # Configuração Pygame - LAYOUT LATERAL
        self.width = 1400
        self.height = 800
        self.spot_width = 50 
        self.spot_height = 100
        self.spot_spacing = 3
        self.road_width = 100
        
        # Estrada horizontal no centro
        self.road_y = self.height // 2 - self.road_width // 2
        
        # Calcular posições das vagas ao longo da estrada
        num_spots_per_side = self.config['NUM_REGULAR_SPOTS'] // 2
        self.parking_start_x = 150
        
        # SHOP no lado direito (destino)
        self.shop_width = 350
        self.shop_height = 100
        self.shop_x = self.width - 280 - self.shop_width - 50
        self.shop_y = 675
        
        # Inicializar Pygame
        pygame.init()
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("E-Mobility Parking Lot - Live Simulation")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 20)
        self.small_font = pygame.font.Font(None, 16)
        self.title_font = pygame.font.Font(None, 24)
        
        # Estado da simulação
        self.paused = False
        self.speed = 1.0
        self.station_positions = {}

    def draw_spot(self, x, y, side):   
        if side == 'top':
            pygame.draw.line(self.screen, (255, 255, 255), (x - 3*self.spot_width/4, y - self.spot_height/2), (x + 3*self.spot_width/4,  y - self.spot_height/2), 2)
            pygame.draw.line(self.screen, (255, 255, 255), (x - 3*self.spot_width/4, y - self.spot_height/2), (x - 3*self.spot_width/4, y + self.spot_height/2), 2)
            pygame.draw.line(self.screen, (255, 255, 255), (x + 3*self.spot_width/4, y - self.spot_height/2), (x + 3*self.spot_width/4, y + self.spot_height/2), 2)
        elif side == 'bottom':
            pygame.draw.line(self.screen, (255, 255, 255), (x - 3*self.spot_width/4, y + self.spot_height/2), (x + 3*self.spot_width/4,  y + self.spot_height/2), 2)
            pygame.draw.line(self.screen, (255, 255, 255), (x - 3*self.spot_width/4, y + self.spot_height/2), (x - 3*self.spot_width/4, y - self.spot_height/2), 2)
            pygame.draw.line(self.screen, (255, 255, 255), (x + 3*self.spot_width/4, y + self.spot_height/2), (x + 3*self.spot_width/4, y - self.spot_height/2), 2)


    def draw_parking_spots(self,inital_x, initial_y, num_spots, side,type):
        for i in range(num_spots):
            self.draw_spot(inital_x + i * 2 * (3*self.spot_width/4), initial_y, side)

        if type == 'regular':
            pass
        elif type == 'CS-Mid':
            self.station_positions['CS-Mid'] = {
            'x': inital_x,                
            'y': initial_y}
        elif type == 'CS-Near':
            self.station_positions['CS-Near'] = {
            'x': 200 - 50,                
            'y': 700 + 50,                
            'width': self.spot_width * 3,
            'height': self.spot_height - 60
            }
        elif type == 'CS-Far':
            self.station_positions['CS-Far'] = {
            'x': 1200 - 50,               
            'y': 300 + 50,                
            'width': self.spot_width * 3, 
            'height': self.spot_height - 60
            }
    
    def draw_road_lines(self, length,y,height):
        gap = 80
        for i in range(length // gap):
            pygame.draw.line(self.screen, YELLOW, (i * gap + 20, y+height//2), (i * gap + 40, y+height//2), 5)

    def draw_road(self,y,width,height):
        pygame.draw.rect(self.screen, DARK_GRAY, (0, y, self.width, height))
        self.draw_road_lines(self.width,y,height)

    def draw_sign(self,x,y,size,color,text_color,text):
        # Draw two sticks (poles) supporting the sign
        pygame.draw.line(self.screen, BLACK, (x + 20, y+size/2), (x + 20, y + size/2 + 30), 4)
        pygame.draw.line(self.screen, BLACK, (x+size - 25, y+size/2), (x + size - 25, y + size/2 + 30), 4)
        pygame.draw.rect(self.screen, color, (x,y, size, size/2))
        font = self.font
        text_surface = font.render(text, True, text_color)
        text_rect = text_surface.get_rect(center=(x + size/2, y + (size/2)/2))

        self.screen.blit(text_surface, text_rect)

    def draw_parking_lot(self):
        # Draw Road
        #self.draw_road(500,self.width,self.road_width)
        
        # Draw Parking Spots
        #self.draw_parking_spots(100,100,10,'top','regular')

        #Draw Charging Stations
        self.draw_parking_spots(700,300,3,'top','CS-Mid')
    
    def draw_vehicle(self, vehicle):
        """Desenha um veículo como retângulo com bordas arredondadas"""
        # Cor baseada no tipo
        if vehicle.is_ev:
            color = GREEN if vehicle.state == VehicleState.PARKED else YELLOW
            dark_color = DARK_GREEN
        else:
            color = BLUE if vehicle.state == VehicleState.PARKED else LIGHT_BLUE
            dark_color = DARK_BLUE
        
        # Tamanho do retângulo
        width = 28
        height = 18
        
        # Calcular ângulo de rotação
        if vehicle.state in [VehicleState.ARRIVING, VehicleState.DEPARTING]:
            # Verificar se ainda tem intermediate (ainda na estrada)
            if hasattr(vehicle, 'intermediate_x') and hasattr(vehicle, 'intermediate_y'):
                # Ainda na estrada, manter horizontal
                angle = 0
            else:
                # Movendo para vaga ou voltando da vaga
                dx = vehicle.target_x - vehicle.x
                dy = vehicle.target_y - vehicle.y
                if abs(dx) > 0.1 or abs(dy) > 0.1:
                    angle = math.atan2(dy, dx)
                else:
                    angle = 0
        else:
            # Carros estacionados ficam perpendiculares à estrada
            road_center = self.road_y + self.road_width // 2

            if vehicle.y < road_center:
                angle = -math.pi / 2  # Virado para cima
            elif vehicle.y > road_center:
                angle = math.pi / 2   # Virado para baixo
            else:
                angle = 0
        
        # Desenhar retângulo arredondado rotacionado
        temp_surface = pygame.Surface((width + 4, height + 4), pygame.SRCALPHA)
        temp_rect = pygame.Rect(2, 2, width, height)
        radius = 4
        
        pygame.draw.rect(temp_surface, color, temp_rect, border_radius=radius)
        pygame.draw.rect(temp_surface, BLACK, temp_rect, 1, border_radius=radius)
        
        # Desenhar janela (sempre mostrar quando não está em movimento na estrada)
        if vehicle.state == VehicleState.PARKED or (vehicle.state == VehicleState.DEPARTING and not hasattr(vehicle, 'intermediate_x')):
            window_size = 8
            window_rect = pygame.Rect(
                (width - window_size) // 2 + 2,
                (height - window_size) // 2 + 2,
                window_size,
                window_size
            )
            pygame.draw.rect(temp_surface, dark_color, window_rect)
        
        # Rotacionar
        if angle != 0:
            temp_surface = pygame.transform.rotate(temp_surface, -math.degrees(angle))
        
        rotated_rect = temp_surface.get_rect(center=(int(vehicle.x), int(vehicle.y)))
        self.screen.blit(temp_surface, rotated_rect)
    
    def draw_stats_panel(self):
        """Desenha o painel de estatísticas"""
        panel_x = self.width - 280
        panel_y = 10
        panel_width = 270
        panel_height = self.height - 20
        
        panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
        pygame.draw.rect(self.screen, DARK_GRAY, panel_rect)
        pygame.draw.rect(self.screen, WHITE, panel_rect, 2)
        
        title = self.title_font.render("Estatisticas", True, WHITE)
        self.screen.blit(title, (panel_x + 10, panel_y + 10))
        
        # Coletar estatísticas
        time = self.parking_lot.env.now
        total_vehicles = self.parking_lot.total_vehicles
        total_evs = self.parking_lot.total_evs
        vehicles_served = self.parking_lot.vehicles_served
        total_revenue = self.parking_lot.total_revenue
        
        evs_at_cs = sum(cs.vehicles_served for cs in self.parking_lot.charging_stations)
        adoption_rate = (evs_at_cs / total_evs * 100) if total_evs > 0 else 0
        ev_percentage = (total_evs/total_vehicles*100) if total_vehicles > 0 else 0
        revenue_per_hour = (total_revenue/(time/60)) if time > 0 else 0
        
        y_offset = 45
        line_height = 22
        
        stats = [
            f"Tempo: {time:.1f} min",
            f"",
            f"Veiculos: {total_vehicles}",
            f"  EVs: {total_evs} ({ev_percentage:.1f}%)",
            f"  Servidos: {vehicles_served}",
            f"",
            f"EVs em CS: {evs_at_cs}",
            f"Adocao: {adoption_rate:.1f}%",
            f"",
            f"Receita: ${total_revenue:.2f}",
            f"Por hora: ${revenue_per_hour:.2f}",
            f"",
            f"Estacoes:",
        ]
        
        for stat in stats:
            text = self.small_font.render(stat, True, WHITE)
            self.screen.blit(text, (panel_x + 10, panel_y + y_offset))
            y_offset += line_height
        
        # Estatísticas por estação
        y_offset += 5
        for cs in self.parking_lot.charging_stations:
            usage_rate = (cs.total_usage_time / (time * cs.num_spots) * 100) if time > 0 else 0
            cs_stat = f"  {cs.name}: {cs.vehicles_served} ({usage_rate:.1f}%)"
            text = self.small_font.render(cs_stat, True, WHITE)
            self.screen.blit(text, (panel_x + 10, panel_y + y_offset))
            y_offset += line_height
        
        # Controles
        y_offset = panel_height - 90
        controls = [
            "Controles:",
            "SPACE: Pausar",
            "UP/DOWN: Velocidade",
            "ESC: Sair"
        ]
        for control in controls:
            text = self.small_font.render(control, True, GRAY)
            self.screen.blit(text, (panel_x + 10, panel_y + y_offset))
            y_offset += line_height
    
    def handle_event(self, event):
        """Processa eventos da simulação"""
        event_type = event.get('type')
        
        if event_type == 'vehicle_arrive':
            vehicle_id = event['vehicle_id']
            is_ev = event['is_ev']
            battery_level = event.get('battery_level')
            
            road_center_y = self.road_y + self.road_width // 2
            vehicle = VehicleVisual(
                id=vehicle_id,
                is_ev=is_ev,
                x=-20,
                y=road_center_y,
                state=VehicleState.ARRIVING,
                battery_level=battery_level,
                target_x=100,
                target_y=road_center_y,
                speed=2.0
            )
            self.vehicles[vehicle_id] = vehicle
            
        elif event_type == 'vehicle_park':
            vehicle_id = event['vehicle_id']
            spot_name = event['spot_name']
            is_cs = event.get('is_cs', False)
            
            if vehicle_id and vehicle_id in self.vehicles:
                vehicle = self.vehicles[vehicle_id]
                vehicle.state = VehicleState.PARKED
                vehicle.spot_name = spot_name
                
                road_center_y = self.road_y + self.road_width // 2
                
                if is_cs:
                    if spot_name == "CS-Mid":
                        pos = self.station_positions[spot_name]

                        cs = next(cs for cs in self.parking_lot.charging_stations if cs.name == spot_name)

                        spot_index = None
                        for i in range(cs.num_spots):
                            spot_key = (cs.name, i)
                            if spot_key not in self.occupied_cs_spots:
                                spot_index = i
                                self.occupied_cs_spots[spot_key] = vehicle_id
                                break

                        if spot_index is None:
                            # All spots full → force use of last spot
                            spot_index = cs.num_spots - 1
                            spot_key = (cs.name, spot_index)
                            if spot_key in self.occupied_cs_spots:
                                old_vehicle_id = self.occupied_cs_spots[spot_key]
                                if old_vehicle_id in self.vehicles:
                                    del self.vehicles[old_vehicle_id]
                            self.occupied_cs_spots[spot_key] = vehicle_id
                        
                        # Spot Center
                        spot_x = pos['x'] + spot_index * self.spot_width
                        spot_y = pos['y']

                        vehicle.intermediate_x = spot_x
                        vehicle.intermediate_y = road_center_y
                        vehicle.target_x = spot_x
                        vehicle.target_y = spot_y

                elif spot_name == "CS-Near":
                    # pos = self.station_positions[spot_name]
                    # cs = next(cs for cs in self.parking_lot.charging_stations if cs.name == spot_name)

                    # # Prefer middle spot
                    # spot_order = [1, 0, 2]
                    # spot_index = None
                    # for i in spot_order:
                    #     spot_key = (cs.name, i)
                    #     if spot_key not in self.occupied_cs_spots:
                    #         self.occupied_cs_spots[spot_key] = vehicle_id
                    #         spot_index = i
                    #         break

                    # if spot_index is None:
                    #     spot_index = cs.num_spots - 1
                    #     spot_key = (cs.name, spot_index)
                    #     if spot_key in self.occupied_cs_spots:
                    #         old_vehicle = self.occupied_cs_spots[spot_key]
                    #         if old_vehicle in self.vehicles:
                    #             del self.vehicles[old_vehicle]
                    #     self.occupied_cs_spots[spot_key] = vehicle_id

                    # # --- EXACT CENTER OF SPOT BASED ON YOUR DRAWING ---
                    # spot_x = pos['x'] + (spot_index + 0.5) * self.spot_width
                    # spot_y = pos['base_y'] + self.spot_height // 2 + 10   # <── CORRECT OFFSET

                    # vehicle.intermediate_x = spot_x
                    # vehicle.intermediate_y = road_center_y
                    # vehicle.target_x = spot_x
                    # vehicle.target_y = spot_y
                    pass
                    

                else:
                    num_spots_per_side = self.config['NUM_REGULAR_SPOTS'] // 2
                    
                    spot_found = False
                    for side in range(2):
                        for col in range(num_spots_per_side):
                            spot_key = (side, col)
                            if spot_key not in self.occupied_regular_spots:
                                self.occupied_regular_spots[spot_key] = vehicle_id
                                
                                spot_x = self.parking_start_x -50 + col * (self.spot_width + self.spot_spacing) + self.spot_width // 2
                                
                                vehicle.intermediate_x = spot_x
                                vehicle.intermediate_y = road_center_y
                                vehicle.target_x = spot_x
                                
                                if side == 0:
                                    vehicle.target_y = self.road_y - self.spot_height - 25 + self.spot_height // 2
                                else:
                                    vehicle.target_y = self.road_y + self.road_width + 25 + self.spot_height // 2
                                
                                spot_found = True
                                break
                        if spot_found:
                            break
                    
                    if not spot_found:
                        spot_num = hash(vehicle_id) % self.config['NUM_REGULAR_SPOTS']
                        side = spot_num // num_spots_per_side
                        col = spot_num % num_spots_per_side
                        spot_key = (side, col)
                        
                        if spot_key in self.occupied_regular_spots:
                            old_vehicle_id = self.occupied_regular_spots[spot_key]
                            if old_vehicle_id in self.vehicles:
                                del self.vehicles[old_vehicle_id]
                        
                        self.occupied_regular_spots[spot_key] = vehicle_id
                        
                        spot_x = self.parking_start_x - 50 + col * (self.spot_width + self.spot_spacing) + self.spot_width // 2
                        
                        vehicle.intermediate_x = spot_x
                        vehicle.intermediate_y = road_center_y
                        vehicle.target_x = spot_x
                        
                        if side == 0:
                            vehicle.target_y = self.road_y - self.spot_height - 25 + self.spot_height // 2
                        else:
                            vehicle.target_y = self.road_y + self.road_width + 25 + self.spot_height // 2
        
        elif event_type == 'vehicle_depart':
            vehicle_id = event['vehicle_id']
            if vehicle_id in self.vehicles:
                vehicle = self.vehicles[vehicle_id]
                vehicle.state = VehicleState.DEPARTING
                
                road_center_y = self.road_y + self.road_width // 2
                
                vehicle.intermediate_x = vehicle.x
                vehicle.intermediate_y = road_center_y
                vehicle.target_x = self.width
                vehicle.target_y = road_center_y
                
                if vehicle.spot_name:
                    if vehicle.spot_name == "Regular":
                        for spot_key, vid in list(self.occupied_regular_spots.items()):
                            if vid == vehicle_id:
                                del self.occupied_regular_spots[spot_key]
                                break
                    else:
                        for spot_key, vid in list(self.occupied_cs_spots.items()):
                            if vid == vehicle_id:
                                del self.occupied_cs_spots[spot_key]
                                break
        
        elif event_type == 'vehicle_remove':
            vehicle_id = event['vehicle_id']
            if vehicle_id in self.vehicles:
                vehicle = self.vehicles[vehicle_id]
                
                if vehicle.spot_name:
                    if vehicle.spot_name == "Regular":
                        for spot_key, vid in list(self.occupied_regular_spots.items()):
                            if vid == vehicle_id:
                                del self.occupied_regular_spots[spot_key]
                                break
                    else:
                        for spot_key, vid in list(self.occupied_cs_spots.items()):
                            if vid == vehicle_id:
                                del self.occupied_cs_spots[spot_key]
                                break
                
                del self.vehicles[vehicle_id]
    
    def update_vehicles(self):
        """Atualiza posições dos veículos (animação com movimento em duas fases)"""
        for vehicle in self.vehicles.values():
            if vehicle.state in [VehicleState.ARRIVING, VehicleState.DEPARTING]:
                if hasattr(vehicle, 'intermediate_x') and hasattr(vehicle, 'intermediate_y'):
                    dx_inter = vehicle.intermediate_x - vehicle.x
                    dy_inter = vehicle.intermediate_y - vehicle.y
                    distance_inter = math.sqrt(dx_inter*dx_inter + dy_inter*dy_inter)
                    
                    if distance_inter > vehicle.speed:
                        vehicle.x += (dx_inter / distance_inter) * vehicle.speed * self.speed
                        vehicle.y += (dy_inter / distance_inter) * vehicle.speed * self.speed
                    else:
                        vehicle.x = vehicle.intermediate_x
                        vehicle.y = vehicle.intermediate_y
                        delattr(vehicle, 'intermediate_x')
                        delattr(vehicle, 'intermediate_y')
                else:
                    dx = vehicle.target_x - vehicle.x
                    dy = vehicle.target_y - vehicle.y
                    distance = math.sqrt(dx*dx + dy*dy)
                    
                    if distance > vehicle.speed:
                        vehicle.x += (dx / distance) * vehicle.speed * self.speed
                        vehicle.y += (dy / distance) * vehicle.speed * self.speed
                    else:
                        vehicle.x = vehicle.target_x
                        vehicle.y = vehicle.target_y
            
            elif vehicle.state == VehicleState.PARKED:
                if hasattr(vehicle, 'intermediate_x') and hasattr(vehicle, 'intermediate_y'):
                    dx_inter = vehicle.intermediate_x - vehicle.x
                    dy_inter = vehicle.intermediate_y - vehicle.y
                    distance_inter = math.sqrt(dx_inter*dx_inter + dy_inter*dy_inter)
                    
                    if distance_inter > vehicle.speed:
                        vehicle.x += (dx_inter / distance_inter) * vehicle.speed * self.speed
                        vehicle.y += (dy_inter / distance_inter) * vehicle.speed * self.speed
                    else:
                        vehicle.x = vehicle.intermediate_x
                        vehicle.y = vehicle.intermediate_y
                        delattr(vehicle, 'intermediate_x')
                        delattr(vehicle, 'intermediate_y')
                else:
                    dx = vehicle.target_x - vehicle.x
                    dy = vehicle.target_y - vehicle.y
                    distance = math.sqrt(dx*dx + dy*dy)
                    
                    if distance > 1:
                        vehicle.x += (dx / distance) * vehicle.speed * self.speed
                        vehicle.y += (dy / distance) * vehicle.speed * self.speed
                    else:
                        vehicle.x = vehicle.target_x
                        vehicle.y = vehicle.target_y
    
    def run(self):
        """Loop principal da visualização"""
        print("🎮 Visualização Pygame iniciada!")
        print("   Controles: SPACE (pausar), UP/DOWN (velocidade), ESC (sair)")
        
        running = True
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_SPACE:
                        self.paused = not self.paused
                        print(f"   {'⏸️  Pausado' if self.paused else '▶️  Retomado'}")
                    elif event.key == pygame.K_UP:
                        self.speed = min(self.speed + 0.5, 3.0)
                        print(f"   Velocidade: {self.speed:.1f}x")
                    elif event.key == pygame.K_DOWN:
                        self.speed = max(self.speed - 0.5, 0.5)
                        print(f"   Velocidade: {self.speed:.1f}x")
            
            while not self.event_queue.empty():
                try:
                    event = self.event_queue.get_nowait()
                    self.handle_event(event)
                except queue.Empty:
                    break
            
            if not self.paused:
                self.update_vehicles()
            
            self.screen.fill(PARKING_GRAY)
            
            for vehicle in self.vehicles.values():
                self.draw_vehicle(vehicle)
            
            self.draw_parking_lot()
            self.draw_stats_panel()
            
            pygame.display.flip()
            self.clock.tick(60)
        
        self.running = False
        pygame.quit()
        print("🎮 Visualização encerrada")
    
    def close(self):
        """Fecha a visualização"""
        self.running = False


def create_visualizer(parking_lot, config):
    """Factory function para criar visualizador Pygame"""
    return ParkingLotVisualizerPygame(parking_lot, config)