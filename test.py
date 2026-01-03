import pygame
import parking_lot
import queue

DAYS_OF_WEEK = ["Sunday", "Monday", "Tuesday", "Wednesday",
                "Thursday", "Friday", "Saturday"]

SIM_START_DAY = 0
SIM_START_HOUR = 8


class visualizer:
    def __init__(self):
        self.event_queue = queue.Queue()
        self.running = True
        self.paused = False

        self.screen_width = 1400
        self.screen_height = 800

        pygame.init()
        self.screen = pygame.display.set_mode(
            (self.screen_width, self.screen_height)
        )
        pygame.display.set_caption("Parking Lot Simulation")

        self.clock = pygame.time.Clock()
        self.fps = 60
        self.font = pygame.font.SysFont("Arial", 30, bold=True)

        self.parking_lot = parking_lot.parkingLot(
            self.screen,
            self.screen_width,
            self.screen_height,
            (100, 400)
        )

        # Set later by simulation
        self.env = None
        self.sim_start_day = SIM_START_DAY
        self.sim_start_hour = SIM_START_HOUR

    def handle_event(self, event):
        if event["type"] == "arrival":
            self.parking_lot.add_vehicle(event["vehicle"])

    def get_sim_clock(self):
        """Convert env.now (minutes) → day + HH:MM"""
        sim_minutes = self.env.now
        total_minutes = self.sim_start_hour * 60 + sim_minutes

        day_index = int(
            (self.sim_start_day + total_minutes // (24 * 60)) % 7
        )
        minutes_today = total_minutes % (24 * 60)

        hour = int(minutes_today // 60)
        minute = int(minutes_today % 60)

        return DAYS_OF_WEEK[day_index], f"{hour:02d}:{minute:02d}"

    def draw_clock(self):
        if self.env is None:
            return

        day, time_str = self.get_sim_clock()
        surface = self.font.render(
            f"{day} {time_str}", True, (255, 255, 255)
        )
        self.screen.blit(surface, (20, 20))

    def run(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                    elif event.key == pygame.K_SPACE:
                        self.paused = not self.paused

            while not self.event_queue.empty():
                try:
                    self.handle_event(self.event_queue.get_nowait())
                except queue.Empty:
                    break

            if not self.paused:
                self.parking_lot.update()

            self.screen.fill((30, 30, 30))
            self.parking_lot.draw_parking_lot()
            #self.parking_lot.display_grid()
            self.draw_clock()

            pygame.display.flip()
            self.clock.tick(self.fps)

        pygame.quit()


def create_visualizer():
    return visualizer()
