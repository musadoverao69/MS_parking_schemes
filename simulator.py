"""
MAIN SIMULATOR - E-Mobility Parking Lot

Complete simulator with all features:
- 4 Allocation Schemes (ON_DEMAND, EXCLUSIVE, PRIORITY, RESERVATION)
- Charging Stations at different locations
- EV battery levels
- Differentiated pricing
- Driver economic profiles

Triple trade-off: Distance × Battery × Price
"""
import simpy
import random
from typing import List

# Import classes and configuration
from models import (
    AllocationScheme,
    BatteryLevel,
    EconomicProfile,
    ChargingStation,
    generate_battery_level,
    generate_economic_profile
)
from config import *


class ParkingLot:
    """Parking lot with Charging Stations and complete allocation system"""
    
    def __init__(self, env, scheme):
        self.env = env
        self.scheme = scheme
        self.regular_spots = simpy.Resource(env, capacity=NUM_REGULAR_SPOTS)
        self.regular_price = REGULAR_SPOT_PRICE
        
        # Create charging stations
        self.charging_stations: List[ChargingStation] = []
        for i, (name, distance, num_spots, price) in enumerate(CHARGING_STATIONS_CONFIG):
            cs = ChargingStation(
                id=i, name=name,
                distance_from_entrance=distance,
                num_spots=num_spots,
                price_per_hour=price,
                resource=simpy.Resource(env, capacity=num_spots),
                resource_priority=simpy.PriorityResource(env, capacity=num_spots)
            )
            self.charging_stations.append(cs)
        
        self.charging_stations.sort(key=lambda cs: cs.distance_from_entrance)
        self.total_ev_spots = sum(cs.num_spots for cs in self.charging_stations)
        
        # Statistics
        self.total_vehicles = 0
        self.total_evs = 0
        self.vehicles_served = 0
        self.evs_served = 0
        self.evs_chose_regular_distance = 0
        self.evs_chose_regular_battery_ok = 0
        self.evs_chose_regular_price = 0
        self.regular_used_ev = 0
        self.total_wait_time = 0
        self.ev_wait_time = 0
        self.regular_wait_time = 0
        self.num_ev_waits = 0
        self.num_regular_waits = 0
        self.total_revenue = 0.0
        self.regular_revenue = 0.0
        self.ev_revenue = 0.0
    
    def choose_charging_station(self, battery_level, economic_profile):
        """Choose best CS based on distance, battery and price"""
        max_distance = DISTANCE_TOLERANCE_BY_BATTERY[battery_level]
        price_tolerance_battery = PRICE_TOLERANCE_BY_BATTERY[battery_level]
        price_tolerance_profile = PRICE_TOLERANCE_BY_PROFILE[economic_profile]
        final_price_tolerance = price_tolerance_battery * price_tolerance_profile
        max_price = REGULAR_SPOT_PRICE * (final_price_tolerance / 100)
        
        for cs in self.charging_stations:
            if cs.distance_from_entrance > max_distance:
                cs.distance_rejections += 1
                continue
            if cs.price_per_hour > max_price:
                cs.price_rejections += 1
                continue
            
            resource = cs.resource_priority if self.scheme == AllocationScheme.RESERVATION else cs.resource
            if resource.count < resource.capacity or len(resource.queue) < 2:
                return cs
        
        return None
    
    def print_status(self):
        """Print current status"""
        print(f"\n[Time {self.env.now:.0f}min] Status:")
        print(f"  Regular spots (${self.regular_price:.2f}/h): {self.regular_spots.count}/{self.regular_spots.capacity}")
        print(f"  Charging Stations:")
        for cs in self.charging_stations:
            resource = cs.resource_priority if self.scheme == AllocationScheme.RESERVATION else cs.resource
            print(f"    {cs.name} ({cs.distance_from_entrance}m, ${cs.price_per_hour:.2f}/h): "
                  f"{resource.count}/{cs.num_spots} occupied, queue: {len(resource.queue)}")


def vehicle_process(env, name, parking_lot, is_ev, battery_level=None, economic_profile=None, has_reservation=False):
    """Vehicle process at parking lot"""
    arrival = env.now
    scheme = parking_lot.scheme
    spot = None
    charging_station = None
    use_priority = False
    priority = 1
    chosen_price = parking_lot.regular_price
    
    if is_ev and battery_level and economic_profile:
        # EV decision logic
        charging_station = parking_lot.choose_charging_station(battery_level, economic_profile)
        
        if scheme == AllocationScheme.EXCLUSIVE:
            # EXCLUSIVE: Only uses CS
            if charging_station:
                spot = charging_station.resource
                chosen_price = charging_station.price_per_hour
            else:
                charging_station = parking_lot.charging_stations[0]
                spot = charging_station.resource
                chosen_price = charging_station.price_per_hour
        
        elif scheme == AllocationScheme.ON_DEMAND:
            # ON_DEMAND: Tries CS, can use regular
            if charging_station:
                spot = charging_station.resource
                chosen_price = charging_station.price_per_hour
            else:
                spot = parking_lot.regular_spots
                charging_station = None
                parking_lot.evs_chose_regular_battery_ok += 1
        
        elif scheme == AllocationScheme.PRIORITY:
            # PRIORITY: EV has priority
            if charging_station:
                spot = charging_station.resource
                chosen_price = charging_station.price_per_hour
            else:
                spot = parking_lot.regular_spots
                charging_station = None
                parking_lot.evs_chose_regular_battery_ok += 1
        
        elif scheme == AllocationScheme.RESERVATION:
            # RESERVATION: With priority
            if charging_station:
                spot = charging_station.resource_priority
                use_priority = True
                priority = 0 if has_reservation else 1
                chosen_price = charging_station.price_per_hour
            else:
                spot = parking_lot.regular_spots
                charging_station = None
                parking_lot.evs_chose_regular_battery_ok += 1
    
    else:
        # Regular vehicle
        if scheme == AllocationScheme.PRIORITY:
            if parking_lot.regular_spots.count < parking_lot.regular_spots.capacity:
                spot = parking_lot.regular_spots
            else:
                for cs in parking_lot.charging_stations:
                    if cs.resource.count < cs.resource.capacity and len(cs.resource.queue) == 0:
                        spot = cs.resource
                        charging_station = cs
                        chosen_price = cs.price_per_hour
                        parking_lot.regular_used_ev += 1
                        break
                if not spot:
                    spot = parking_lot.regular_spots
        else:
            spot = parking_lot.regular_spots
    
    # Process parking
    try:
        if use_priority:
            with spot.request(priority=priority) as request:
                yield request
                yield from process_stay(env, parking_lot, is_ev, arrival, chosen_price, charging_station)
        else:
            with spot.request() as request:
                yield request
                yield from process_stay(env, parking_lot, is_ev, arrival, chosen_price, charging_station)
    except simpy.Interrupt:
        pass


def process_stay(env, parking_lot, is_ev, arrival, chosen_price, charging_station):
    """Process parking duration and statistics"""
    wait_time = env.now - arrival
    parking_lot.total_wait_time += wait_time
    
    if is_ev:
        parking_lot.ev_wait_time += wait_time
        parking_lot.num_ev_waits += 1
    else:
        parking_lot.regular_wait_time += wait_time
        parking_lot.num_regular_waits += 1
    
    parking_duration = random.randint(*PARKING_TIME)
    yield env.timeout(parking_duration)
    
    # Calculate cost
    hours = parking_duration / 60.0
    cost = hours * chosen_price
    
    # Update statistics
    if charging_station:
        charging_station.vehicles_served += 1
        charging_station.total_usage_time += parking_duration
        charging_station.total_revenue += cost
        parking_lot.ev_revenue += cost
    else:
        parking_lot.regular_revenue += cost
    
    parking_lot.total_revenue += cost
    parking_lot.vehicles_served += 1
    if is_ev:
        parking_lot.evs_served += 1


def vehicle_generator(env, parking_lot):
    """Generates vehicles arriving at parking lot"""
    counter = 0
    
    while True:
        yield env.timeout(random.expovariate(1.0 / ARRIVAL_INTERVAL))
        
        counter += 1
        is_ev = random.random() < PROB_EV
        battery_level = None
        economic_profile = None
        has_reservation = False
        
        if is_ev:
            battery_level = generate_battery_level()
            economic_profile = generate_economic_profile()
            if parking_lot.scheme == AllocationScheme.RESERVATION:
                has_reservation = random.random() < PROB_RESERVATION
        
        parking_lot.total_vehicles += 1
        if is_ev:
            parking_lot.total_evs += 1
        
        env.process(vehicle_process(env, f'V-{counter}', parking_lot, is_ev, 
                                   battery_level, economic_profile, has_reservation))


def status_monitor(env, parking_lot, interval=120):
    """Monitor status periodically"""
    while True:
        yield env.timeout(interval)
        parking_lot.print_status()


def print_configuration():
    """Print simulation configuration"""
    print("=" * 100)
    print("E-MOBILITY PARKING SIMULATOR - Charging Stations System")
    print("=" * 100)
    print(f"\n⚙️  CONFIGURATION:")
    print(f"  Scheme: {ALLOCATION_SCHEME.value.upper()}")
    print(f"  Regular spots: {NUM_REGULAR_SPOTS} (${REGULAR_SPOT_PRICE:.2f}/h)")
    print(f"\n  Charging Stations:")
    for name, dist, spots, price in CHARGING_STATIONS_CONFIG:
        print(f"    • {name}: {spots} spots, {dist}m, ${price:.2f}/h")
    print(f"\n  Parameters:")
    print(f"    • Time: {SIMULATION_TIME}min ({SIMULATION_TIME/60:.1f}h)")
    print(f"    • EV probability: {PROB_EV*100:.0f}%")
    print(f"    • Arrival interval: {ARRIVAL_INTERVAL}min")
    print("=" * 100)


def print_results(parking_lot):
    """Print final results"""
    print("\n" + "=" * 100)
    print("FINAL RESULTS")
    print("=" * 100)
    
    print(f"\n📊 VEHICLES:")
    print(f"  Total: {parking_lot.total_vehicles} ({parking_lot.total_evs} EVs)")
    print(f"  Served: {parking_lot.vehicles_served} ({parking_lot.evs_served} EVs)")
    
    print(f"\n⏱️  WAIT TIMES:")
    if parking_lot.num_ev_waits > 0:
        print(f"  EVs: {parking_lot.ev_wait_time / parking_lot.num_ev_waits:.2f} min")
    if parking_lot.num_regular_waits > 0:
        print(f"  Regular: {parking_lot.regular_wait_time / parking_lot.num_regular_waits:.2f} min")
    
    print(f"\n🔌 CHARGING STATIONS:")
    for cs in parking_lot.charging_stations:
        usage_rate = (cs.total_usage_time / (SIMULATION_TIME * cs.num_spots)) * 100 if cs.total_usage_time > 0 else 0
        print(f"\n  {cs.name} ({cs.distance_from_entrance}m, ${cs.price_per_hour:.2f}/h):")
        print(f"    Served: {cs.vehicles_served} | Usage: {usage_rate:.1f}% | Revenue: ${cs.total_revenue:.2f}")
        print(f"    Rejections: {cs.distance_rejections} (distance) + {cs.price_rejections} (price)")
    
    print(f"\n💰 FINANCIAL:")
    print(f"  Total revenue: ${parking_lot.total_revenue:.2f}")
    print(f"    • Regular spots: ${parking_lot.regular_revenue:.2f} "
          f"({parking_lot.regular_revenue/parking_lot.total_revenue*100 if parking_lot.total_revenue > 0 else 0:.1f}%)")
    print(f"    • EV spots: ${parking_lot.ev_revenue:.2f} "
          f"({parking_lot.ev_revenue/parking_lot.total_revenue*100 if parking_lot.total_revenue > 0 else 0:.1f}%)")
    print(f"  Revenue/hour: ${parking_lot.total_revenue/(SIMULATION_TIME/60):.2f}")
    
    print(f"\n🚗 DECISIONS:")
    evs_at_cs = sum(cs.vehicles_served for cs in parking_lot.charging_stations)
    print(f"  EVs at CS: {evs_at_cs}/{parking_lot.total_evs} "
          f"({evs_at_cs/parking_lot.total_evs*100 if parking_lot.total_evs > 0 else 0:.1f}%)")
    print(f"  EVs at regular: {parking_lot.evs_chose_regular_battery_ok + parking_lot.evs_chose_regular_price}")
    
    print("=" * 100)


def run_simulation(verbose=True):
    """
    Run a complete simulation
    
    Args:
        verbose: If True, print detailed logs
    
    Returns:
        ParkingLot with collected statistics
    """
    random.seed(RANDOM_SEED)
    env = simpy.Environment()
    parking_lot = ParkingLot(env, ALLOCATION_SCHEME)
    
    env.process(vehicle_generator(env, parking_lot))
    if verbose:
        env.process(status_monitor(env, parking_lot, interval=120))
    
    env.run(until=SIMULATION_TIME)
    
    return parking_lot


def main():
    """Main function"""
    print_configuration()
    parking_lot = run_simulation(verbose=False)
    print_results(parking_lot)


if __name__ == '__main__':
    main()

