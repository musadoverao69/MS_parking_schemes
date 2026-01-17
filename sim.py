import simpy
import random
import threading
import time
from vehicle import vehicle as Vehicle
from test_viz import create_visualizer

class ParkingSimulation:
    def __init__(self, num_regular_spots=20, num_ev_spots=6, ev_scheme="on_demand", static_pricing=True,alpha=1.0,base_rate=2.0):
        
        # Configuration
        self.num_regular_spots = num_regular_spots
        self.num_ev_spots = num_ev_spots
        self.ev_scheme = ev_scheme
        self.static_pricing = static_pricing
        self.sim_speed = 1
        self.random_seed = 42
        
        # Economic & Energy Config (Portugal 2026)
        self.cost_per_ev_plug = 2500
        self.electricity_price = 0.15   # Cost to lot owner per kWh
        self.charging_markup = 0.25     # Price sold to customer per kWh
        self.setup_cost = self.num_ev_spots * self.cost_per_ev_plug

        # Constants
        self.MEAN_PARK_TIME = 90
        self.SIM_MINUTES_TO_VISUAL_SECONDS = 0.05
        self.SIMULATION_TIME = 7 * 24 * 60
        self.OPEN_HOUR = 9
        self.CLOSE_HOUR = 22
        self.BASE_RATE = base_rate
        self.ALPHA = alpha
        self.SIM_START_DAY = 0
        self.SIM_START_HOUR = 8
        self.total_parked_minutes = 0

        # State / Results
        self.arrival_times = []
        self.park_times = []
        self.accepted_ev = 0
        self.rejected_ev_full = 0
        self.rejected_ev_price = 0
        self.accepted_ice = 0
        self.rejected_ice_full = 0
        self.rejected_ice_price = 0
        
        # Revenue Breakdown
        self.revenue_ice = 0.0
        self.revenue_ev_parking = 0.0  # Money from the spot
        self.revenue_ev_charging = 0.0 # Profit from electricity

    def get_average_fullness(self):
            total_capacity = self.num_regular_spots + self.num_ev_spots
            
            # Calculate hours per day the lot is actually open
            open_hours_per_day = self.CLOSE_HOUR - self.OPEN_HOUR
            
            # Total days in simulation (e.g., 7)
            total_days = self.SIMULATION_TIME / (24 * 60)
            
            # Total minutes the lot was actually open across the whole sim
            active_potential_minutes = total_capacity * (open_hours_per_day * 60) * total_days
            
            if active_potential_minutes == 0: 
                return 0
                
            # Fullness = (Actual Minutes Used) / (Minutes available during business hours)
            fullness = self.total_parked_minutes / active_potential_minutes
            
            # Cap at 1.0 (In case a car stays slightly past closing time)
            return min(1.0, fullness)
    
    def arrival_rate(self, sim_day, sim_minute):
        hour = int(sim_minute // 60)
        if sim_day in range(1, 6): # Weekdays
            rates = {9: 0.15, 10: 0.175, 11: 0.2, 12: 0.225, 13: 0.25, 14: 0.275, 
                     15: 0.3, 16: 0.325, 17: 0.35, 18: 0.4, 19: 0.35, 20: 0.3, 21: 0.2}
            self.avg_arrival = sum(rates.values()) / len(rates)
            return rates.get(hour, 0)
        else: # Weekend
            rates = {9: 0.2, 10: 0.225, 11: 0.25, 12: 0.275, 13: 0.3, 14: 0.35, 
                     15: 0.4, 16: 0.45, 17: 0.5, 18: 0.45, 19: 0.5, 20: 0.35, 21: 0.3}
            self.avg_arrival = sum(rates.values()) / len(rates)
            return rates.get(hour, 0)

    def minutes_until_next_open(self, sim_minute):
        hour = sim_minute // 60
        if hour < self.OPEN_HOUR:
            return self.OPEN_HOUR * 60 - sim_minute
        else:
            return (24 * 60 - sim_minute) + self.OPEN_HOUR * 60

    def get_random_wtp(self):
        # Mean of $2.00 with sigma 0.4
        return random.lognormvariate(mu=0.61, sigma=0.4)

    def compute_price(self, lam):
        if self.static_pricing:
            return self.BASE_RATE
        else:
            return self.BASE_RATE * self.ALPHA * (1 + (lam - self.avg_arrival))

    def calculate_charging_profit(self, vehicle, duration_min):
        """Calculates energy profit using existing Vehicle attributes"""
        energy_needed = vehicle.battery_capacity * (1.0 - vehicle.soc_arrival)
        max_deliverable = (duration_min / 60) * vehicle.charge_rate
        
        actual_kwh = min(energy_needed, max_deliverable)
        return actual_kwh * (self.charging_markup - self.electricity_price)

    def vehicle_process(self, env, vehicle, parking_resource, visualizer=None):
        # Time Sync
        sim_day = (self.SIM_START_DAY + int(env.now // (24 * 60))) % 7
        sim_minute = (self.SIM_START_HOUR * 60 + env.now) % (24 * 60)
        lam = self.arrival_rate(sim_day, sim_minute)
        
        # 1. Price check vs WTP
        price_per_hour = self.compute_price(lam)
        vehicle.max_wtp = self.get_random_wtp() # Assigning WTP at gate

        if vehicle.max_wtp < price_per_hour:
            if vehicle.is_ev: self.rejected_ev_price += 1
            else: self.rejected_ice_price += 1
            return

        # 2. Allocation Logic
        resource = None
        if vehicle.is_ev:
            if self.ev_scheme in ["priority", "on_demand"]:
                if parking_resource.ev_spots.count < parking_resource.ev_spots.capacity:
                    resource = parking_resource.ev_spots
                elif parking_resource.regular_spots.count < parking_resource.regular_spots.capacity:
                    resource = parking_resource.regular_spots
            else: # Exclusive
                if parking_resource.ev_spots.count < parking_resource.ev_spots.capacity:
                    resource = parking_resource.ev_spots
            
            if not resource: 
                self.rejected_ev_full += 1
                return
        else:
            if self.ev_scheme == "on_demand":
                if parking_resource.regular_spots.count < parking_resource.regular_spots.capacity:
                    resource = parking_resource.regular_spots
                elif parking_resource.ev_spots.count < parking_resource.ev_spots.capacity:
                    resource = parking_resource.ev_spots
            else:
                if parking_resource.regular_spots.count < parking_resource.regular_spots.capacity:
                    resource = parking_resource.regular_spots
            
            if not resource: 
                self.rejected_ice_full += 1
                return

        # 3. Successful Parking
        if vehicle.is_ev: self.accepted_ev += 1
        else: self.accepted_ice += 1

        # Determine duration and revenue
        park_duration_hours = max(1, random.gauss(self.MEAN_PARK_TIME, self.MEAN_PARK_TIME * 0.3)) / 60
        vehicle.park_duration = park_duration_hours * 60
        self.park_times.append(vehicle.park_duration)

        parking_revenue = price_per_hour * park_duration_hours
        
        if vehicle.is_ev:
            self.revenue_ev_parking += parking_revenue
            # Only add charging profit if they used an actual EV spot
            if resource == parking_resource.ev_spots:
                self.revenue_ev_charging += self.calculate_charging_profit(vehicle, vehicle.park_duration)
        else:
            self.revenue_ice += parking_revenue

        # Simulation Block
        with resource.request() as req:
            yield req
            if visualizer: visualizer.event_queue.put({"type": "arrival", "vehicle": vehicle})
            yield env.timeout(vehicle.park_duration)
            self.total_parked_minutes += vehicle.park_duration # Add this line
            if visualizer: visualizer.event_queue.put({"type": "depart", "vehicle": vehicle})

    def vehicle_generator(self, env, parking_resource, visualizer=None):
        vehicle_id = 0
        while True:
            sim_day = (self.SIM_START_DAY + int(env.now // (24 * 60))) % 7
            sim_minute = (self.SIM_START_HOUR * 60 + env.now) % (24 * 60)
            hour = sim_minute // 60

            if hour < self.OPEN_HOUR or hour >= self.CLOSE_HOUR:
                yield env.timeout(self.minutes_until_next_open(sim_minute))
                continue

            lam = self.arrival_rate(sim_day, sim_minute)
            if lam <= 0:
                yield env.timeout(1)
                continue

            yield env.timeout(random.expovariate(lam)/4)

            vehicle_id += 1
            # Vehicle init uses your custom attributes
            v = Vehicle(screen=None, id=vehicle_id, is_ev=random.random() < 0.3,
                        speed=2.0, state="arriving", position=(0, 450))
            
            self.arrival_times.append(env.now)
            env.process(self.vehicle_process(env, v, parking_resource, visualizer))

    def run(self, visualize=False):
        random.seed(self.random_seed)
        env = simpy.Environment()
        
        class ParkingResource:
            def __init__(self, env, num_reg, num_ev):
                self.regular_spots = simpy.Resource(env, capacity=num_reg)
                self.ev_spots = simpy.Resource(env, capacity=num_ev)

        parking_resource = ParkingResource(env, self.num_regular_spots, self.num_ev_spots)
        visualizer = create_visualizer() if visualize else None

        if visualizer:
            visualizer.env = env
            visualizer.sim_speed = self.sim_speed
            visualizer.sim_start_day = self.SIM_START_DAY
            visualizer.sim_start_hour = self.SIM_START_HOUR

        env.process(self.vehicle_generator(env, parking_resource, visualizer))

        if visualize:
            def sim_thread():
                step = 0.5
                t = 0.0
                while visualizer.running and t < self.SIMULATION_TIME:
                    env.run(until=min(t + step, self.SIMULATION_TIME))
                    t += step
                    time.sleep(step * self.SIM_MINUTES_TO_VISUAL_SECONDS / self.sim_speed)

            threading.Thread(target=sim_thread, daemon=True).start()
            visualizer.run()
        else:
            env.run(until=self.SIMULATION_TIME)

if __name__ == "__main__":
    sim = ParkingSimulation(num_regular_spots=20, num_ev_spots=6, ev_scheme="on_demand", static_pricing=False, alpha=1.5, base_rate=2.0)
    sim.run(visualize=True)