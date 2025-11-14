"""
MAIN SIMULATOR - E-Mobility Parking Lot

Complete simulator with all features:
- 2 Allocation Schemes (ON_DEMAND, RESERVATION)
- Charging Stations at different locations
- EV battery levels
- Differentiated pricing
- Driver economic profiles

Triple trade-off: Distance × Battery × Price
"""
import simpy
import random
import argparse
from typing import List, Optional

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
    
    def __init__(self, env, scheme, visualizer=None):
        self.env = env
        self.scheme = scheme
        self.visualizer = visualizer
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
    
    # Print arrival
    vehicle_type = "EV" if is_ev else "Regular"
    if is_ev and battery_level and economic_profile:
        vehicle_type = f"EV ({battery_level.value}/{economic_profile.value})"
    print(f"[{env.now:6.1f}min] {name:8s} ({vehicle_type:20s}) arrived")
    
    # Notify visualizer
    if parking_lot.visualizer:
        parking_lot.visualizer.add_event({
            'type': 'vehicle_arrive',
            'vehicle_id': name,
            'is_ev': is_ev,
            'battery_level': battery_level.value if battery_level else None
        })
    
    if is_ev and battery_level and economic_profile:
        # EV decision logic
        charging_station = parking_lot.choose_charging_station(battery_level, economic_profile)
        
        if scheme == AllocationScheme.ON_DEMAND:
            # ON_DEMAND: Tries CS, can use regular
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
        # Regular vehicle - only uses regular spots
        spot = parking_lot.regular_spots
    
    # Process parking
    try:
        if use_priority:
            with spot.request(priority=priority) as request:
                yield request
                yield from process_stay(env, name, parking_lot, is_ev, arrival, chosen_price, charging_station)
        else:
            with spot.request() as request:
                yield request
                yield from process_stay(env, name, parking_lot, is_ev, arrival, chosen_price, charging_station)
    except simpy.Interrupt:
        pass


def process_stay(env, vehicle_name, parking_lot, is_ev, arrival, chosen_price, charging_station):
    """Process parking duration and statistics"""
    wait_time = env.now - arrival
    parking_lot.total_wait_time += wait_time
    
    # Print parking action
    spot_name = charging_station.name if charging_station else "Regular"
    if wait_time > 0:
        print(f"[{env.now:6.1f}min]          → Parked at {spot_name:12s} (${chosen_price:.2f}/h) [waited {wait_time:.1f}min]")
    else:
        print(f"[{env.now:6.1f}min]          → Parked at {spot_name:12s} (${chosen_price:.2f}/h)")
    
    # Notify visualizer
    if parking_lot.visualizer:
        parking_lot.visualizer.add_event({
            'type': 'vehicle_park',
            'vehicle_id': vehicle_name,
            'spot_name': spot_name,
            'is_cs': charging_station is not None
        })
    
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
    
    # Print departure
    print(f"[{env.now:6.1f}min]          ← Departed from {spot_name:12s} (stayed {parking_duration}min, paid ${cost:.2f})")
    
    # Notify visualizer
    if parking_lot.visualizer:
        parking_lot.visualizer.add_event({
            'type': 'vehicle_depart',
            'vehicle_id': vehicle_name
        })
    
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
        print("\n" + "─" * 100)
        parking_lot.print_status()
        
        # Print running statistics
        if parking_lot.total_evs > 0:
            evs_at_cs = sum(cs.vehicles_served for cs in parking_lot.charging_stations)
            adoption = (evs_at_cs / parking_lot.total_evs) * 100 if parking_lot.total_evs > 0 else 0
            print(f"\n  📊 Running Stats:")
            print(f"     EVs arrived: {parking_lot.total_evs} | At CS: {evs_at_cs} ({adoption:.1f}%)")
            if parking_lot.num_ev_waits > 0:
                avg_wait = parking_lot.ev_wait_time / parking_lot.num_ev_waits
                print(f"     Avg EV wait: {avg_wait:.2f} min | Revenue: ${parking_lot.total_revenue:.2f}")
        print("─" * 100 + "\n")


def print_configuration():
    """Print simulation configuration"""
    print("\n" + "=" * 100)
    print("🚗⚡ E-MOBILITY PARKING SIMULATOR - Charging Stations System")
    print("=" * 100)
    print(f"\n⚙️  CONFIGURATION:")
    print(f"  Allocation Scheme: {ALLOCATION_SCHEME.value.upper()}")
    print(f"  Regular spots: {NUM_REGULAR_SPOTS} (${REGULAR_SPOT_PRICE:.2f}/h)")
    
    total_ev_spots = sum(spots for _, _, spots, _ in CHARGING_STATIONS_CONFIG)
    print(f"\n  🔌 Charging Stations (Total: {total_ev_spots} EV spots):")
    for name, dist, spots, price in CHARGING_STATIONS_CONFIG:
        print(f"    • {name:12s}: {spots} spots at {dist:3.0f}m from entrance, ${price:5.2f}/h")
    
    print(f"\n  📊 Simulation Parameters:")
    print(f"    • Duration: {SIMULATION_TIME}min ({SIMULATION_TIME/60:.1f} hours)")
    print(f"    • EV probability: {PROB_EV*100:.0f}%")
    print(f"    • Arrival interval: {ARRIVAL_INTERVAL}min (avg)")
    print(f"    • Expected vehicles: ~{int(SIMULATION_TIME/ARRIVAL_INTERVAL)}")
    print(f"    • Expected EVs: ~{int(SIMULATION_TIME/ARRIVAL_INTERVAL*PROB_EV)}")
    
    print(f"\n  🎯 Decision Model:")
    print(f"    • Battery levels: 4 (CRITICAL, LOW, MEDIUM, HIGH)")
    print(f"    • Economic profiles: 3 (BUDGET, MODERATE, PREMIUM)")
    print(f"    • Trade-off: Distance × Battery × Price")
    
    print("=" * 100)
    print("🚀 Starting simulation...")
    print("=" * 100 + "\n")


def print_results(parking_lot):
    """Print final results"""
    print("\n" + "=" * 100)
    print("📊 FINAL RESULTS - SIMULATION COMPLETE")
    print("=" * 100)
    
    # Calculate key metrics first
    evs_at_cs = sum(cs.vehicles_served for cs in parking_lot.charging_stations)
    adoption_rate = (evs_at_cs / parking_lot.total_evs * 100) if parking_lot.total_evs > 0 else 0
    service_rate = (parking_lot.vehicles_served / parking_lot.total_vehicles * 100) if parking_lot.total_vehicles > 0 else 0
    
    print(f"\n📊 VEHICLES:")
    print(f"  Total arrived: {parking_lot.total_vehicles}")
    print(f"    • Electric vehicles (EVs): {parking_lot.total_evs} ({parking_lot.total_evs/parking_lot.total_vehicles*100:.1f}%)")
    print(f"    • Regular vehicles: {parking_lot.total_vehicles - parking_lot.total_evs} ({(parking_lot.total_vehicles-parking_lot.total_evs)/parking_lot.total_vehicles*100:.1f}%)")
    print(f"\n  Total served: {parking_lot.vehicles_served} (Service rate: {service_rate:.1f}%)")
    print(f"    • EVs served: {parking_lot.evs_served}")
    print(f"    • Regular served: {parking_lot.vehicles_served - parking_lot.evs_served}")
    
    print(f"\n⏱️  WAIT TIMES:")
    if parking_lot.num_ev_waits > 0:
        avg_ev_wait = parking_lot.ev_wait_time / parking_lot.num_ev_waits
        print(f"  EVs average: {avg_ev_wait:.2f} min")
        if avg_ev_wait < 5:
            print(f"    ✅ Excellent service (< 5 min)")
        elif avg_ev_wait < 15:
            print(f"    ✓  Good service (< 15 min)")
        else:
            print(f"    ⚠️  Poor service (> 15 min)")
    if parking_lot.num_regular_waits > 0:
        print(f"  Regular average: {parking_lot.regular_wait_time / parking_lot.num_regular_waits:.2f} min")
    
    print(f"\n🔌 CHARGING STATIONS PERFORMANCE:")
    total_cs_rejections_dist = 0
    total_cs_rejections_price = 0
    
    for i, cs in enumerate(parking_lot.charging_stations, 1):
        usage_rate = (cs.total_usage_time / (SIMULATION_TIME * cs.num_spots)) * 100 if cs.total_usage_time > 0 else 0
        total_cs_rejections_dist += cs.distance_rejections
        total_cs_rejections_price += cs.price_rejections
        
        # Usage assessment
        usage_status = "🟢 Good" if 60 <= usage_rate <= 80 else ("🟡 Low" if usage_rate < 60 else "🔴 High")
        
        print(f"\n  {i}. {cs.name} ({cs.distance_from_entrance:.0f}m from entrance, ${cs.price_per_hour:.2f}/h):")
        print(f"     Vehicles served: {cs.vehicles_served}")
        print(f"     Utilization: {usage_rate:.1f}% {usage_status}")
        print(f"     Revenue: ${cs.total_revenue:.2f}")
        if cs.vehicles_served > 0:
            avg_revenue = cs.total_revenue / cs.vehicles_served
            print(f"     Revenue per vehicle: ${avg_revenue:.2f}")
        print(f"     Rejections: {cs.distance_rejections} (too far) + {cs.price_rejections} (too expensive)")
        
        # Insights
        if cs.vehicles_served == 0:
            print(f"     ⚠️  WARNING: No usage! Consider relocating or repricing")
        elif usage_rate > 90:
            print(f"     💡 High demand! Consider adding more spots here")
    
    print(f"\n💰 FINANCIAL ANALYSIS:")
    print(f"  Total revenue: ${parking_lot.total_revenue:.2f}")
    print(f"    • Regular spots: ${parking_lot.regular_revenue:.2f} "
          f"({parking_lot.regular_revenue/parking_lot.total_revenue*100 if parking_lot.total_revenue > 0 else 0:.1f}%)")
    print(f"    • EV spots (CS): ${parking_lot.ev_revenue:.2f} "
          f"({parking_lot.ev_revenue/parking_lot.total_revenue*100 if parking_lot.total_revenue > 0 else 0:.1f}%)")
    
    revenue_per_hour = parking_lot.total_revenue/(SIMULATION_TIME/60)
    print(f"\n  Revenue per hour: ${revenue_per_hour:.2f}")
    print(f"  Daily projection (24h): ${revenue_per_hour * 24:.2f}")
    print(f"  Monthly projection (30d): ${revenue_per_hour * 24 * 30:.2f}")
    
    if parking_lot.vehicles_served > 0:
        print(f"  Average per vehicle: ${parking_lot.total_revenue/parking_lot.vehicles_served:.2f}")
    
    print(f"\n🚗 EV DECISIONS & BEHAVIOR:")
    print(f"  EVs at Charging Stations: {evs_at_cs}/{parking_lot.total_evs} ({adoption_rate:.1f}%)")
    if adoption_rate >= 70:
        print(f"    ✅ Good CS adoption rate")
    elif adoption_rate >= 50:
        print(f"    ⚠️  Moderate CS adoption")
    else:
        print(f"    ❌ Low CS adoption - check pricing/location")
    
    evs_at_regular = parking_lot.evs_chose_regular_battery_ok + parking_lot.evs_chose_regular_price
    print(f"  EVs at regular spots: {evs_at_regular} ({evs_at_regular/parking_lot.total_evs*100 if parking_lot.total_evs > 0 else 0:.1f}%)")
    if parking_lot.evs_chose_regular_battery_ok > 0:
        print(f"    • Battery OK (didn't need charging): {parking_lot.evs_chose_regular_battery_ok}")
    if parking_lot.evs_chose_regular_price > 0:
        print(f"    • Rejected CS due to price: {parking_lot.evs_chose_regular_price}")
    
    print(f"\n  Total rejections:")
    print(f"    • Distance rejections: {total_cs_rejections_dist}")
    print(f"    • Price rejections: {total_cs_rejections_price}")
    
    if total_cs_rejections_price > total_cs_rejections_dist:
        print(f"    💡 INSIGHT: Price matters MORE than distance!")
    elif total_cs_rejections_dist > total_cs_rejections_price:
        print(f"    💡 INSIGHT: Distance matters MORE than price!")
    
    print("\n" + "=" * 100)
    print("✅ Simulation completed successfully!")
    print("=" * 100)


def run_simulation(verbose=True, show_vehicles=False, visualize=False):
    """
    Run a complete simulation
    
    Args:
        verbose: If True, show periodic status updates
        show_vehicles: If True, print each vehicle arrival/departure
        visualize: If True, show real-time visualization
    
    Returns:
        ParkingLot with collected statistics
    """
    random.seed(RANDOM_SEED)
    env = simpy.Environment()
    
    # Create parking lot first
    parking_lot = ParkingLot(env, ALLOCATION_SCHEME)
    
    # Create visualizer if requested
    visualizer = None
    if visualize:
        try:
            from visualizer_pygame import create_visualizer
            config_dict = {
                'NUM_REGULAR_SPOTS': NUM_REGULAR_SPOTS,
                'CHARGING_STATIONS_CONFIG': CHARGING_STATIONS_CONFIG
            }
            visualizer = create_visualizer(parking_lot, config_dict)
            parking_lot.visualizer = visualizer
            print("🎮 Visualização Pygame ativada!")
        except ImportError:
            print("⚠️  Pygame não instalado.")
            print("   Execute: pip install pygame")
            visualize = False
    
    env.process(vehicle_generator(env, parking_lot))
    if verbose:
        env.process(status_monitor(env, parking_lot, interval=120))
    
    # Progress indicator
    if not show_vehicles and not visualize:
        print("Simulating", end="", flush=True)
    
    # Run simulation
    if visualize:
        # Pygame: rodar em thread separada
        import threading
        import time
        
        def run_simulation():
            """Roda a simulação em thread separada"""
            step_size = 0.5  # Passos menores para simulação mais lenta
            current_time = 0.0
            
            while current_time < SIMULATION_TIME and visualizer.running:
                next_time = min(current_time + step_size, SIMULATION_TIME)
                env.run(until=next_time)
                current_time = next_time
                time.sleep(0.05)  # Delay maior para simulação mais lenta
        
        # Iniciar simulação em thread
        sim_thread = threading.Thread(target=run_simulation, daemon=True)
        sim_thread.start()
        
        # Rodar visualização (bloqueia até fechar)
        try:
            visualizer.run()
        except KeyboardInterrupt:
            print("\n⏹️  Simulação interrompida")
        finally:
            visualizer.close()
    else:
        env.run(until=SIMULATION_TIME)
    
    if not show_vehicles and not visualize:
        print(" ✓\n")
    
    return parking_lot


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='E-Mobility Parking Lot Simulator')
    parser.add_argument('--visualize', '-v', action='store_true',
                       help='Show real-time visualization')
    parser.add_argument('--verbose', action='store_true',
                       help='Show detailed logs')
    parser.add_argument('--show-vehicles', action='store_true',
                       help='Show each vehicle arrival/departure')
    
    args = parser.parse_args()
    
    print_configuration()
    
    # Run simulation
    parking_lot = run_simulation(
        verbose=args.verbose, 
        show_vehicles=args.show_vehicles,
        visualize=args.visualize
    )
    
    # Print results (skip if visualizing, as it may still be running)
    if not args.visualize:
        print_results(parking_lot)
    
    # Additional insights
    print("\n💡 KEY INSIGHTS:")
    evs_at_cs = sum(cs.vehicles_served for cs in parking_lot.charging_stations)
    
    # Most popular CS
    if parking_lot.charging_stations:
        most_popular = max(parking_lot.charging_stations, key=lambda cs: cs.vehicles_served)
        print(f"  • Most popular CS: {most_popular.name} ({most_popular.vehicles_served} vehicles)")
        
        # Most profitable CS
        most_profitable = max(parking_lot.charging_stations, key=lambda cs: cs.total_revenue)
        print(f"  • Most profitable CS: {most_profitable.name} (${most_profitable.total_revenue:.2f})")
        
        # Least used CS
        least_used = min(parking_lot.charging_stations, key=lambda cs: cs.vehicles_served)
        if least_used.vehicles_served == 0:
            print(f"  • ⚠️  {least_used.name} had ZERO usage - consider removing or relocating")
    
    # CS adoption assessment
    adoption = (evs_at_cs / parking_lot.total_evs * 100) if parking_lot.total_evs > 0 else 0
    if adoption > 80:
        print(f"  • ✅ Excellent CS adoption ({adoption:.1f}%)")
    elif adoption > 60:
        print(f"  • ✓  Good CS adoption ({adoption:.1f}%)")
    else:
        print(f"  • ⚠️  Low CS adoption ({adoption:.1f}%) - Review pricing or location")
    
    print("\n" + "=" * 100)


if __name__ == '__main__':
    main()

