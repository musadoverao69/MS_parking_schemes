"""
Visualizador Pygame para Parking Lot Simulation

Visualização estilo highway-env com vista de cima:
- Layout organizado com linhas delimitando vagas
- Quadradinhos representando carros
- Estações de carregamento claramente definidas
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
PARKING_GRAY = (40, 40, 40)  # Cor do asfalto


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
    angle: float = 0  # Rotação do veículo


class ParkingLotVisualizerPygame:
    """Visualizador do parking lot usando Pygame - Vista de cima"""
    
    def __init__(self, parking_lot, config):
        self.parking_lot = parking_lot
        self.config = config
        
        # Queue para comunicação com SimPy
        self.event_queue = queue.Queue()
        self.running = True
        
        # Dados de visualização
        self.vehicles: Dict[str, VehicleVisual] = {}
        
        # Rastreamento de vagas ocupadas
        self.occupied_regular_spots: Dict[tuple, str] = {}  # {(row, col): vehicle_id}
        self.occupied_cs_spots: Dict[tuple, str] = {}  # {(cs_name, spot_index): vehicle_id}
        
        # Configuração Pygame
        self.width = 1400
        self.height = 800
        self.spot_width = 35
        self.spot_height = 60
        self.spot_spacing = 3
        self.corridor_width = 80  # Largura do corredor entre fileiras
        
        # Calcular posições centralizadas
        num_spots_per_row = self.config['NUM_REGULAR_SPOTS'] // 2
        total_parking_width = num_spots_per_row * (self.spot_width + self.spot_spacing)
        
        # Centralizar estacionamento (considerando painel de 280px)
        available_width = self.width - 280  # Largura disponível (sem painel)
        self.parking_start_x = (available_width // 2) - total_parking_width // 2
        self.parking_start_y = 150
        
        # SHOP centralizado com o estacionamento (não com a tela)
        self.shop_width = 200
        self.shop_height = 60
        parking_center_x = self.parking_start_x + total_parking_width // 2
        self.shop_x = parking_center_x - self.shop_width // 2
        self.shop_y = 30
        
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
        
        # Calcular posições das estações
        self.setup_station_positions()
    
    def setup_station_positions(self):
        """Calcula posições das estações de carregamento (na mesma linha do SHOP, sem sobrepor)"""
        self.station_positions = {}
        
        # Posicionar estações à direita do SHOP (sem sobrepor)
        spacing_between = 25  # Reduzir espaçamento para caber mais estações
        start_x = self.shop_x + self.shop_width + spacing_between
        
        # Verificar limite do painel
        panel_start_x = self.width - 280
        max_station_x = panel_start_x - 30  # Margem maior
        
        # Calcular largura total necessária
        total_width_needed = sum(
            cs.num_spots * (self.spot_width + self.spot_spacing) - self.spot_spacing
            for cs in self.parking_lot.charging_stations
        )
        total_spacing = spacing_between * (len(self.parking_lot.charging_stations) - 1)
        total_needed = total_width_needed + total_spacing
        available_space = max_station_x - start_x
        
        # Se não couber, reduzir espaçamento
        if total_needed > available_space and len(self.parking_lot.charging_stations) > 1:
            spacing_between = max(15, (available_space - total_width_needed) // (len(self.parking_lot.charging_stations) - 1))
        
        # Posicionar cada estação sequencialmente à direita do SHOP
        current_x = start_x
        for cs in self.parking_lot.charging_stations:
            station_width = cs.num_spots * (self.spot_width + self.spot_spacing) - self.spot_spacing
            
            # Verificar se cabe antes do painel
            if current_x + station_width > max_station_x:
                # Ajustar para caber (colocar o mais próximo possível)
                x = max(start_x, max_station_x - station_width - 10)
            else:
                x = current_x
            
            # Mesma altura do SHOP
            y = self.shop_y
            
            # SEMPRE adicionar ao dicionário (mesmo que não caiba perfeitamente)
            self.station_positions[cs.name] = {
                'x': x,
                'y': y,
                'width': station_width,
                'height': self.spot_height
            }
            
            # Próxima estação
            current_x += station_width + spacing_between
    
    def draw_parking_spot(self, x, y, occupied=False, is_ev_spot=False):
        """Desenha uma vaga de estacionamento (estilo da imagem - apenas linhas)"""
        # Na imagem, as vagas são delimitadas apenas por linhas brancas
        # Não preenchemos o fundo (já é o asfalto escuro)
        
        # Linhas brancas delimitando a vaga
        # Linha superior
        pygame.draw.line(
            self.screen, WHITE,
            (x, y),
            (x + self.spot_width, y),
            2
        )
        # Linha inferior
        pygame.draw.line(
            self.screen, WHITE,
            (x, y + self.spot_height),
            (x + self.spot_width, y + self.spot_height),
            2
        )
        # Linha esquerda
        pygame.draw.line(
            self.screen, WHITE,
            (x, y),
            (x, y + self.spot_height),
            2
        )
        # Linha direita
        pygame.draw.line(
            self.screen, WHITE,
            (x + self.spot_width, y),
            (x + self.spot_width, y + self.spot_height),
            2
        )
    
    def draw_regular_parking_area(self):
        """Desenha a área de vagas regulares - duas fileiras principais (estilo da imagem)"""
        # Duas fileiras principais (como na imagem)
        num_rows = 2
        spots_per_row = self.config['NUM_REGULAR_SPOTS'] // num_rows
        
        start_x = self.parking_start_x
        top_row_y = self.parking_start_y
        bottom_row_y = self.parking_start_y + self.spot_height + self.corridor_width
        
        # Fileira superior: linha horizontal longa com linhas verticais descendo
        line_start_x = start_x
        line_end_x = start_x + spots_per_row * (self.spot_width + self.spot_spacing)
        line_y = top_row_y
        
        # Linha horizontal superior (contínua)
        pygame.draw.line(
            self.screen, WHITE,
            (line_start_x, line_y),
            (line_end_x, line_y),
            2
        )
        
        # Linhas verticais descendo (delimitando cada vaga)
        for col in range(spots_per_row + 1):
            x = start_x + col * (self.spot_width + self.spot_spacing)
            pygame.draw.line(
                self.screen, WHITE,
                (x, line_y),
                (x, line_y + self.spot_height),
                2
            )
        
        # Verificar ocupação e desenhar carros na fileira superior
        for col in range(spots_per_row):
            x = start_x + col * (self.spot_width + self.spot_spacing)
            y = top_row_y
            
            # Verificar se está ocupado
            occupied = False
            for vehicle in self.vehicles.values():
                if (vehicle.state == VehicleState.PARKED and 
                    vehicle.spot_name == "Regular" and
                    abs(vehicle.x - (x + self.spot_width // 2)) < self.spot_width // 2 and
                    abs(vehicle.y - (y + self.spot_height // 2)) < self.spot_height // 2):
                    occupied = True
                    break
        
        # Corredor entre as fileiras
        corridor_rect = pygame.Rect(
            start_x - 20,
            top_row_y + self.spot_height,
            spots_per_row * (self.spot_width + self.spot_spacing) + 40,
            self.corridor_width
        )
        
        # Seta no corredor (apontando para a esquerda)
        arrow_x = corridor_rect.centerx - 30
        arrow_y = corridor_rect.centery
        arrow_points = [
            (arrow_x, arrow_y),
            (arrow_x + 20, arrow_y - 10),
            (arrow_x + 20, arrow_y + 10)
        ]
        pygame.draw.polygon(self.screen, WHITE, arrow_points)
        
        # Fileira inferior: linha horizontal longa com linhas verticais subindo
        bottom_line_y = bottom_row_y + self.spot_height
        
        # Linha horizontal inferior (contínua)
        pygame.draw.line(
            self.screen, WHITE,
            (line_start_x, bottom_line_y),
            (line_end_x, bottom_line_y),
            2
        )
        
        # Linhas verticais subindo (delimitando cada vaga)
        for col in range(spots_per_row + 1):
            x = start_x + col * (self.spot_width + self.spot_spacing)
            pygame.draw.line(
                self.screen, WHITE,
                (x, bottom_row_y),
                (x, bottom_line_y),
                2
            )
        
        # Verificar ocupação e desenhar carros na fileira inferior
        for col in range(spots_per_row):
            x = start_x + col * (self.spot_width + self.spot_spacing)
            y = bottom_row_y
            
            # Verificar se está ocupado
            occupied = False
            for vehicle in self.vehicles.values():
                if (vehicle.state == VehicleState.PARKED and 
                    vehicle.spot_name == "Regular" and
                    abs(vehicle.x - (x + self.spot_width // 2)) < self.spot_width // 2 and
                    abs(vehicle.y - (y + self.spot_height // 2)) < self.spot_height // 2):
                    occupied = True
                    break
    
    def draw_charging_station(self, cs):
        """Desenha uma estação de carregamento"""
        # Verificar se a estação está no dicionário
        if cs.name not in self.station_positions:
            return  # Pular se não foi posicionada
        
        pos = self.station_positions[cs.name]
        x = pos['x']
        y = pos['y']
        
        # Desenhar vagas da estação
        for i in range(cs.num_spots):
            spot_x = x + i * (self.spot_width + self.spot_spacing)
            occupied = i < cs.resource.count
            self.draw_parking_spot(spot_x, y, occupied, is_ev_spot=True)
        
        # Label da estação
        label_y = y - 25
        name_text = self.font.render(cs.name, True, WHITE)
        self.screen.blit(name_text, (x, label_y))
        
        # Informações
        info_y = y + self.spot_height + 5
        info_text = self.small_font.render(
            f"{cs.distance_from_entrance}m | ${cs.price_per_hour:.1f}/h", 
            True, LIGHT_GRAY
        )
        self.screen.blit(info_text, (x, info_y))
    
    def draw_entrance(self):
        """Desenha a entrada do shopping (SHOP centralizado com o estacionamento)"""
        # Desenhar retângulo arredondado (simulado com retângulo normal)
        shop_rect = pygame.Rect(self.shop_x, self.shop_y, self.shop_width, self.shop_height)
        pygame.draw.rect(self.screen, WHITE, shop_rect, 3)  # Apenas borda
        
        # Texto "SHOP"
        shop_text = self.title_font.render("SHOP", True, WHITE)
        shop_text_rect = shop_text.get_rect(center=(self.shop_x + self.shop_width // 2, self.shop_y + self.shop_height // 2))
        self.screen.blit(shop_text, shop_text_rect)
        
        # Pequeno bloco amarelo abaixo do SHOP (entrada)
        entrance_block = pygame.Rect(self.shop_x + self.shop_width // 2 - 10, self.shop_y + self.shop_height, 20, 15)
        pygame.draw.rect(self.screen, YELLOW, entrance_block)
    
    def draw_vehicle(self, vehicle):
        """Desenha um veículo como retângulo com bordas arredondadas"""
        # Cor baseada no tipo
        if vehicle.is_ev:
            color = GREEN if vehicle.state == VehicleState.PARKED else YELLOW
            dark_color = DARK_GREEN
        else:
            color = BLUE if vehicle.state == VehicleState.PARKED else LIGHT_BLUE
            dark_color = DARK_BLUE
        
        # Tamanho do retângulo (carro) - mais fino e mais longo
        if vehicle.state == VehicleState.PARKED:
            width = 32  # Mais longo
            height = 14  # Mais fino
        else:
            width = 32  # Mais longo
            height = 14  # Mais fino
        
        # Calcular ângulo de rotação baseado na direção
        if vehicle.state in [VehicleState.ARRIVING, VehicleState.DEPARTING]:
            dx = vehicle.target_x - vehicle.x
            dy = vehicle.target_y - vehicle.y
            if abs(dx) > 0.1 or abs(dy) > 0.1:
                angle = math.atan2(dy, dx)
            else:
                angle = 0
        else:
            # Carros estacionados ficam verticais (perpendiculares às vagas)
            # Fileira superior: carros virados para baixo (90 graus)
            # Fileira inferior: carros virados para cima (-90 graus)
            # Estações: também verticais
            if vehicle.spot_name == "Regular":
                # Determinar fileira baseado na posição Y do veículo
                top_row_center = self.parking_start_y + self.spot_height // 2
                bottom_row_center = self.parking_start_y + self.spot_height + self.corridor_width + self.spot_height // 2
                middle_y = (top_row_center + bottom_row_center) / 2
                
                if vehicle.y < middle_y:
                    # Fileira superior: virado para baixo (90 graus)
                    angle = math.pi / 2
                else:
                    # Fileira inferior: virado para cima (-90 graus)
                    angle = -math.pi / 2
            else:
                # Estações de carregamento: vertical também (virado para baixo)
                angle = math.pi / 2  # 90 graus
        
        # Desenhar retângulo arredondado rotacionado
        # Criar uma superfície temporária para desenhar o retângulo arredondado
        temp_surface = pygame.Surface((width + 4, height + 4), pygame.SRCALPHA)
        temp_rect = pygame.Rect(2, 2, width, height)
        radius = 4  # Raio das bordas arredondadas
        
        # Desenhar retângulo arredondado na superfície temporária
        pygame.draw.rect(temp_surface, color, temp_rect, border_radius=radius)
        pygame.draw.rect(temp_surface, BLACK, temp_rect, 1, border_radius=radius)
        
        # Desenhar janela (quadrado escuro no centro) - estilo da imagem
        if vehicle.state == VehicleState.PARKED:
            window_size = 8
            window_rect = pygame.Rect(
                (width - window_size) // 2 + 2,
                (height - window_size) // 2 + 2,
                window_size,
                window_size
            )
            pygame.draw.rect(temp_surface, dark_color, window_rect)
        
        # Rotacionar a superfície temporária
        if angle != 0:
            temp_surface = pygame.transform.rotate(temp_surface, -math.degrees(angle))
        
        # Obter o retângulo da superfície rotacionada
        rotated_rect = temp_surface.get_rect(center=(int(vehicle.x), int(vehicle.y)))
        
        # Desenhar na tela principal
        self.screen.blit(temp_surface, rotated_rect)
    
    def draw_stats_panel(self):
        """Desenha o painel de estatísticas com bordas arredondadas e fundo transparente"""
        panel_x = self.width - 280
        panel_y = 10
        panel_width = 270
        panel_height = self.height - 20
        border_radius = 15  # Raio para bordas arredondadas
        
        # Criar superfície com transparência para o fundo
        panel_surface = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        
        # Fundo semi-transparente (mais transparente) - usar RGBA
        bg_color = (*DARK_GRAY, 200)  # Alpha = 200 (de 255) para mais transparência
        pygame.draw.rect(panel_surface, bg_color, (0, 0, panel_width, panel_height), border_radius=border_radius)
        
        # Borda mais suave e menos marcada - usar RGBA
        border_color = (*LIGHT_GRAY, 120)  # Cinza claro com transparência (menos marcada)
        pygame.draw.rect(panel_surface, border_color, (0, 0, panel_width, panel_height), width=1, border_radius=border_radius)
        
        # Aplicar superfície na tela
        self.screen.blit(panel_surface, (panel_x, panel_y))
        
        # Título
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
        
        # Estatísticas
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
            
            # Posição inicial (vindo do topo, perto do SHOP - centralizado com estacionamento)
            vehicle = VehicleVisual(
                id=vehicle_id,
                is_ev=is_ev,
                x=self.shop_x + self.shop_width // 2,  # Começa no centro do SHOP
                y=100,  # Vem do topo
                state=VehicleState.ARRIVING,
                battery_level=battery_level,
                target_x=self.shop_x + self.shop_width // 2,  # Primeiro alvo: centro do SHOP
                target_y=100,
                speed=1.5  # Velocidade mais lenta
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
                
                # Calcular posição do spot
                if is_cs:
                    for cs in self.parking_lot.charging_stations:
                        if cs.name == spot_name:
                            if cs.name not in self.station_positions:
                                break
                            pos = self.station_positions[cs.name]
                            
                            # Encontrar uma vaga livre nesta estação
                            spot_index = None
                            for i in range(cs.num_spots):
                                spot_key = (cs.name, i)
                                if spot_key not in self.occupied_cs_spots:
                                    spot_index = i
                                    self.occupied_cs_spots[spot_key] = vehicle_id
                                    break
                            
                            # Se não encontrou vaga livre, usar a última (fallback)
                            if spot_index is None:
                                spot_index = cs.num_spots - 1
                                spot_key = (cs.name, spot_index)
                                # Remover carro anterior se houver
                                if spot_key in self.occupied_cs_spots:
                                    old_vehicle_id = self.occupied_cs_spots[spot_key]
                                    if old_vehicle_id in self.vehicles:
                                        del self.vehicles[old_vehicle_id]
                                self.occupied_cs_spots[spot_key] = vehicle_id
                            
                            vehicle.target_x = pos['x'] + spot_index * (self.spot_width + self.spot_spacing) + self.spot_width // 2
                            vehicle.target_y = pos['y'] + self.spot_height // 2
                            break
                else:
                    # Vaga regular - encontrar uma vaga livre
                    num_rows = 2
                    spots_per_row = self.config['NUM_REGULAR_SPOTS'] // num_rows
                    
                    # Tentar encontrar vaga livre
                    spot_found = False
                    for row in range(num_rows):
                        for col in range(spots_per_row):
                            spot_key = (row, col)
                            if spot_key not in self.occupied_regular_spots:
                                # Vaga livre encontrada
                                self.occupied_regular_spots[spot_key] = vehicle_id
                                
                                vehicle.target_x = self.parking_start_x + col * (self.spot_width + self.spot_spacing) + self.spot_width // 2
                                
                                # Fileira superior ou inferior
                                if row == 0:
                                    vehicle.target_y = self.parking_start_y + self.spot_height // 2
                                else:
                                    vehicle.target_y = self.parking_start_y + self.spot_height + self.corridor_width + self.spot_height // 2
                                
                                spot_found = True
                                break
                        if spot_found:
                            break
                    
                    # Se não encontrou vaga livre, usar hash (fallback)
                    if not spot_found:
                        spot_num = hash(vehicle_id) % self.config['NUM_REGULAR_SPOTS']
                        row = spot_num // spots_per_row
                        col = spot_num % spots_per_row
                        spot_key = (row, col)
                        
                        # Remover carro anterior se houver
                        if spot_key in self.occupied_regular_spots:
                            old_vehicle_id = self.occupied_regular_spots[spot_key]
                            if old_vehicle_id in self.vehicles:
                                del self.vehicles[old_vehicle_id]
                        
                        self.occupied_regular_spots[spot_key] = vehicle_id
                        
                        vehicle.target_x = self.parking_start_x + col * (self.spot_width + self.spot_spacing) + self.spot_width // 2
                        
                        # Fileira superior ou inferior
                        if row == 0:
                            vehicle.target_y = self.parking_start_y + self.spot_height // 2
                        else:
                            vehicle.target_y = self.parking_start_y + self.spot_height + self.corridor_width + self.spot_height // 2
                
                # Não definir posição imediatamente - deixar animar até o spot
                # vehicle.x e vehicle.y serão atualizados pela animação
        
        elif event_type == 'vehicle_depart':
            vehicle_id = event['vehicle_id']
            if vehicle_id in self.vehicles:
                vehicle = self.vehicles[vehicle_id]
                vehicle.state = VehicleState.DEPARTING
                vehicle.target_x = self.shop_x + self.shop_width // 2  # Sair pelo topo (SHOP centralizado)
                vehicle.target_y = 100
                
                # Liberar a vaga ocupada
                if vehicle.spot_name:
                    if vehicle.spot_name == "Regular":
                        # Procurar e remover da lista de vagas regulares ocupadas
                        for spot_key, vid in list(self.occupied_regular_spots.items()):
                            if vid == vehicle_id:
                                del self.occupied_regular_spots[spot_key]
                                break
                    else:
                        # Procurar e remover da lista de vagas de CS ocupadas
                        for spot_key, vid in list(self.occupied_cs_spots.items()):
                            if vid == vehicle_id:
                                del self.occupied_cs_spots[spot_key]
                                break
        
        elif event_type == 'vehicle_remove':
            vehicle_id = event['vehicle_id']
            if vehicle_id in self.vehicles:
                vehicle = self.vehicles[vehicle_id]
                
                # Liberar a vaga ocupada antes de remover
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
        """Atualiza posições dos veículos (animação)"""
        for vehicle in self.vehicles.values():
            if vehicle.state in [VehicleState.ARRIVING, VehicleState.DEPARTING]:
                # Mover em direção ao alvo
                dx = vehicle.target_x - vehicle.x
                dy = vehicle.target_y - vehicle.y
                distance = math.sqrt(dx*dx + dy*dy)
                
                if distance > vehicle.speed:
                    vehicle.x += (dx / distance) * vehicle.speed * self.speed
                    vehicle.y += (dy / distance) * vehicle.speed * self.speed
                else:
                    vehicle.x = vehicle.target_x
                    vehicle.y = vehicle.target_y
                    
                    # Se chegou na entrada e está chegando, mover para o estacionamento
                    if vehicle.state == VehicleState.ARRIVING and vehicle.spot_name:
                        # Já tem destino definido, continuar animando
                        pass
            elif vehicle.state == VehicleState.PARKED:
                # Garantir que carros estacionados fiquem na posição correta
                dx = vehicle.target_x - vehicle.x
                dy = vehicle.target_y - vehicle.y
                distance = math.sqrt(dx*dx + dy*dy)
                
                if distance > 1:
                    # Ainda se movendo para o spot
                    vehicle.x += (dx / distance) * vehicle.speed * self.speed
                    vehicle.y += (dy / distance) * vehicle.speed * self.speed
                else:
                    vehicle.x = vehicle.target_x
                    vehicle.y = vehicle.target_y
    
    def add_event(self, event):
        """Adiciona evento à queue"""
        if self.running:
            self.event_queue.put(event)
    
    def run(self):
        """Loop principal da visualização"""
        print("🎮 Visualização Pygame iniciada!")
        print("   Controles: SPACE (pausar), UP/DOWN (velocidade), ESC (sair)")
        
        running = True
        
        while running:
            # Processar eventos do Pygame
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
            
            # Processar eventos da simulação
            while not self.event_queue.empty():
                try:
                    event = self.event_queue.get_nowait()
                    self.handle_event(event)
                except queue.Empty:
                    break
            
            # Atualizar veículos
            if not self.paused:
                self.update_vehicles()
            
            # Desenhar
            self.screen.fill(PARKING_GRAY)  # Fundo escuro (asfalto)
            
            # Desenhar elementos estáticos (ordem importa para sobreposição)
            self.draw_entrance()  # SHOP primeiro
            for cs in self.parking_lot.charging_stations:
                self.draw_charging_station(cs)  # Estações na mesma linha do SHOP
            self.draw_regular_parking_area()  # Estacionamento abaixo
            
            # Desenhar veículos
            for vehicle in self.vehicles.values():
                self.draw_vehicle(vehicle)
            
            # Desenhar painel de estatísticas
            self.draw_stats_panel()
            
            # Atualizar display
            pygame.display.flip()
            self.clock.tick(60)  # 60 FPS
        
        self.running = False
        pygame.quit()
        print("🎮 Visualização encerrada")
    
    def close(self):
        """Fecha a visualização"""
        self.running = False


def create_visualizer(parking_lot, config):
    """Factory function para criar visualizador Pygame"""
    return ParkingLotVisualizerPygame(parking_lot, config)
