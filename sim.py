# sim_main.py
import simpy
import random
import threading
import time
from vehicle import vehicle as Vehicle
from test import create_visualizer


MEAN_PARK_TIME = 90
NUM_REGULAR_SPOTS = 20
NUM_EV_SPOTS = 6
RANDOM_SEED = 42
SIM_MINUTES_TO_VISUAL_SECONDS = 0.05
SIM_SPEED = 2.0

DAYS_OF_WEEK = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
SIM_START_DAY = 0
SIM_START_HOUR = 8
SIMULATION_TIME = 7 * 24 * 60

OPEN_HOUR = 9
CLOSE_HOUR = 22

EXCLUSIVE = "exclusive"
PRIORITY = "priority"
ON_DEMAND = "on_demand"
EV_SCHEME = ON_DEMAND

BASE_RATE = 5.0 
ALPHA = 1.0  
STATIC_PRICING = True 


arrival_times = []
park_times = []

accepted_ev = 0
rejected_ev = 0
accepted_ice = 0
rejected_ice = 0

revenue_ev = 0.0
revenue_ice = 0.0


def arrival_rate(sim_day, sim_minute):
    hour = int(sim_minute // 60)

    if sim_day in range(1, 6):
        if 9 <= hour < 10: return 0.15
        elif 10 <= hour < 11: return 0.175
        elif 11 <= hour < 12: return 0.2
        elif 12 <= hour < 13: return 0.225
        elif 13 <= hour < 14: return 0.25
        elif 14 <= hour < 15: return 0.275
        elif 15 <= hour < 16: return 0.3
        elif 16 <= hour < 17: return 0.325
        elif 17 <= hour < 18: return 0.35
        elif 18 <= hour < 19: return 0.4
        elif 19 <= hour < 20: return 0.35
        elif 20 <= hour < 21: return 0.3
        elif 21 <= hour < 22: return 0.2
        else: return 0
    else:  # Weekend
        if 9 <= hour < 10: return 0.2
        elif 10 <= hour < 11: return 0.225
        elif 11 <= hour < 12: return 0.25
        elif 12 <= hour < 13: return 0.275
        elif 13 <= hour < 14: return 0.3
        elif 14 <= hour < 15: return 0.35
        elif 15 <= hour < 16: return 0.4
        elif 16 <= hour < 17: return 0.45
        elif 17 <= hour < 18: return 0.5
        elif 18 <= hour < 19: return 0.45
        elif 19 <= hour < 20: return 0.5
        elif 20 <= hour < 21: return 0.35
        elif 21 <= hour < 22: return 0.3
        else: return 0


def minutes_until_next_open(sim_minute):
    hour = sim_minute // 60
    if hour < OPEN_HOUR:
        return OPEN_HOUR * 60 - sim_minute
    else:
        return (24*60 - sim_minute) + OPEN_HOUR * 60


class ParkingResource:
    def __init__(self, env, num_regular, num_ev):
        self.env = env
        self.regular_spots = simpy.Resource(env, capacity=num_regular)
        self.ev_spots = simpy.Resource(env, capacity=num_ev)


def compute_price(is_ev, lam):
    if STATIC_PRICING:
        return BASE_RATE
    else:
        avg_arrival = 0.25  
        return BASE_RATE * ALPHA * (1 + (lam - avg_arrival))

def vehicle_process(env, vehicle, parking_resource, visualizer=None):
    global accepted_ev, rejected_ev, accepted_ice, rejected_ice, revenue_ev, revenue_ice

    sim_day = (SIM_START_DAY + int(env.now // (24*60))) % 7
    sim_minute = (SIM_START_HOUR*60 + env.now) % (24*60)
    lam = arrival_rate(sim_day, sim_minute)

    price_per_hour = compute_price(vehicle.is_ev, lam)

    if vehicle.max_wtp < price_per_hour:
        if vehicle.is_ev:
            rejected_ev += 1
        else:
            rejected_ice += 1
        return

    allocated = False
    is_ev = vehicle.is_ev
    if is_ev:
        if EV_SCHEME == "exclusive":
            if parking_resource.ev_spots.count < parking_resource.ev_spots.capacity:
                resource = parking_resource.ev_spots
                allocated = True
            else:
                rejected_ev += 1
        elif EV_SCHEME == "priority":
            if parking_resource.ev_spots.count < parking_resource.ev_spots.capacity:
                resource = parking_resource.ev_spots
                allocated = True
            elif parking_resource.regular_spots.count < parking_resource.regular_spots.capacity:
                resource = parking_resource.regular_spots
                allocated = True
            else:
                rejected_ev += 1
        elif EV_SCHEME == "on_demand":
            if parking_resource.ev_spots.count < parking_resource.ev_spots.capacity:
                resource = parking_resource.ev_spots
                allocated = True
            elif parking_resource.regular_spots.count < parking_resource.regular_spots.capacity:
                resource = parking_resource.regular_spots
                allocated = True
            else:
                rejected_ev += 1
    else:
        if parking_resource.regular_spots.count < parking_resource.regular_spots.capacity:
            resource = parking_resource.regular_spots
            allocated = True
        elif parking_resource.ev_spots.count < parking_resource.ev_spots.capacity:
            resource = parking_resource.ev_spots
            allocated = True
        else:
            rejected_ice += 1

    if not allocated:
        return

    if is_ev:
        accepted_ev += 1
    else:
        accepted_ice += 1

    park_duration_hours = max(1, random.gauss(MEAN_PARK_TIME, MEAN_PARK_TIME*0.3)) / 60
    if is_ev:
        revenue_ev += price_per_hour * park_duration_hours
    else:
        revenue_ice += price_per_hour * park_duration_hours
    vehicle.park_duration = park_duration_hours*60
    park_times.append(vehicle.park_duration)

    if visualizer:
        visualizer.event_queue.put({"type":"arrival","vehicle":vehicle})

    with resource.request() as req:
        yield req
        yield env.timeout(vehicle.park_duration)

    if visualizer:
        visualizer.event_queue.put({"type":"depart","vehicle":vehicle})


def vehicle_generator(env, parking_resource, visualizer=None):
    vehicle_id = 0
    while True:
        sim_day = (SIM_START_DAY + int(env.now // (24*60))) % 7
        sim_minute = (SIM_START_HOUR*60 + env.now) % (24*60)
        hour = sim_minute // 60

        if hour < OPEN_HOUR or hour >= CLOSE_HOUR:
            yield env.timeout(minutes_until_next_open(sim_minute))
            continue

        lam = arrival_rate(sim_day, sim_minute)
        if lam <= 0:
            yield env.timeout(1)
            continue

        interarrival = random.expovariate(lam)
        yield env.timeout(interarrival)

        vehicle_id += 1
        # WTP log-normal for right-skew
        max_wtp = random.lognormvariate(mu=1.5, sigma=0.8)
        v = Vehicle(screen=None, id=vehicle_id, is_ev=random.random() < 0.3,
                    speed=2.0, state="arriving", position=(0,450))
        v.max_wtp = max_wtp
        arrival_times.append(env.now)
        env.process(vehicle_process(env, v, parking_resource, visualizer))


def run_simulation(visualize=True):
    random.seed(RANDOM_SEED)
    env = simpy.Environment()
    parking_resource = ParkingResource(env, NUM_REGULAR_SPOTS, NUM_EV_SPOTS)

    visualizer = create_visualizer() if visualize else None
    if visualizer:
        visualizer.env = env
        visualizer.sim_speed = SIM_SPEED
        visualizer.sim_start_day = SIM_START_DAY
        visualizer.sim_start_hour = SIM_START_HOUR

    env.process(vehicle_generator(env, parking_resource, visualizer))

    if visualize:
        def sim_thread():
            step = 0.5
            t = 0.0
            while visualizer.running and t < SIMULATION_TIME:
                env.run(until=min(t+step, SIMULATION_TIME))
                t += step
                time.sleep(step * SIM_MINUTES_TO_VISUAL_SECONDS / SIM_SPEED)

        threading.Thread(target=sim_thread, daemon=True).start()
        visualizer.run()
    else:
        env.run(until=SIMULATION_TIME)


if __name__ == "__main__":
    run_simulation(True)

    total = accepted_ev + rejected_ev + accepted_ice + rejected_ice
    print("=== SIMULATION STATS ===")
    print(f"Total arrivals: {total}")
    print(f"EV accepted/rejected: {accepted_ev} / {rejected_ev}")
    print(f"ICE accepted/rejected: {accepted_ice} / {rejected_ice}")
    if total > 0:
        print(f"EV acceptance rate: {accepted_ev / (accepted_ev + rejected_ev):.2%}")
        print(f"ICE acceptance rate: {accepted_ice / (accepted_ice + rejected_ice):.2%}")
    print(f"EV revenue: ${revenue_ev:.2f}")
    print(f"ICE revenue: ${revenue_ice:.2f}")
    if arrival_times:
        interarrivals = [arrival_times[i+1]-arrival_times[i] for i in range(len(arrival_times)-1)]
        print(f"Mean interarrival: {sum(interarrivals)/len(interarrivals):.2f} min")
    if park_times:
        print(f"Mean parking time: {sum(park_times)/len(park_times):.2f} min")
