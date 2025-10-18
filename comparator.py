"""
GLOBAL COMPARATOR - Complete Scenario Analysis

Compares different combinations of:
- Allocation Schemes
- Charging Station Configurations
- Pricing Strategies

Runs multiple simulations and generates comparative analysis.
"""
import simpy
import random
from typing import List

from models import (
    AllocationScheme,
    BatteryLevel,
    EconomicProfile,
    ChargingStation,
    generate_battery_level,
    generate_economic_profile
)
import config


class ParkingLotComparison:
    """Simplified version for quick comparison"""
    
    def __init__(self, env, cs_config, scheme):
        self.env = env
        self.scheme = scheme
        self.regular_spots = simpy.Resource(env, capacity=config.NUM_REGULAR_SPOTS)
        self.regular_price = config.REGULAR_SPOT_PRICE
        
        self.charging_stations: List[ChargingStation] = []
        for i, (name, distance, num_spots, price) in enumerate(cs_config):
            cs = ChargingStation(
                id=i, name=name, distance_from_entrance=distance,
                num_spots=num_spots, price_per_hour=price,
                resource=simpy.Resource(env, capacity=num_spots),
                resource_priority=simpy.PriorityResource(env, capacity=num_spots)
            )
            self.charging_stations.append(cs)
        
        self.charging_stations.sort(key=lambda cs: cs.distance_from_entrance)
        self.total_ev_spots = sum(cs.num_spots for cs in self.charging_stations)
        
        # Summary statistics
        self.total_evs = 0
        self.evs_served = 0
        self.ev_wait_time = 0
        self.num_ev_waits = 0
        self.total_revenue = 0.0
        self.ev_revenue = 0.0
    
    def choose_charging_station(self, battery_level, economic_profile):
        max_distance = config.DISTANCE_TOLERANCE_BY_BATTERY[battery_level]
        price_tolerance = config.PRICE_TOLERANCE_BY_BATTERY[battery_level] * config.PRICE_TOLERANCE_BY_PROFILE[economic_profile]
        max_price = config.REGULAR_SPOT_PRICE * (price_tolerance / 100)
        
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


def vehicle_quick(env, parking_lot, is_ev, battery_level, economic_profile, has_reservation):
    """Simplified vehicle process for comparison"""
    arrival = env.now
    charging_station = None
    price = parking_lot.regular_price
    use_priority = False
    priority = 1
    
    if is_ev:
        charging_station = parking_lot.choose_charging_station(battery_level, economic_profile)
        if charging_station:
            price = charging_station.price_per_hour
            if parking_lot.scheme == AllocationScheme.RESERVATION:
                spot = charging_station.resource_priority
                use_priority = True
                priority = 0 if has_reservation else 1
            else:
                spot = charging_station.resource
        else:
            spot = parking_lot.regular_spots
            charging_station = None
    else:
        spot = parking_lot.regular_spots
    
    try:
        if use_priority:
            with spot.request(priority=priority) as request:
                yield request
                wait_time = env.now - arrival
                parking_lot.ev_wait_time += wait_time
                parking_lot.num_ev_waits += 1
                duration = random.randint(*config.PARKING_TIME)
                yield env.timeout(duration)
                cost = (duration / 60.0) * price
                if charging_station:
                    charging_station.vehicles_served += 1
                    charging_station.total_revenue += cost
                    parking_lot.ev_revenue += cost
                parking_lot.total_revenue += cost
                parking_lot.evs_served += 1
        else:
            with spot.request() as request:
                yield request
                wait_time = env.now - arrival
                if is_ev:
                    parking_lot.ev_wait_time += wait_time
                    parking_lot.num_ev_waits += 1
                duration = random.randint(*config.PARKING_TIME)
                yield env.timeout(duration)
                cost = (duration / 60.0) * price
                if charging_station:
                    charging_station.vehicles_served += 1
                    charging_station.total_revenue += cost
                    parking_lot.ev_revenue += cost
                parking_lot.total_revenue += cost
                if is_ev:
                    parking_lot.evs_served += 1
    except simpy.Interrupt:
        pass


def vehicle_generator_quick(env, parking_lot):
    counter = 0
    while True:
        yield env.timeout(random.expovariate(1.0 / config.ARRIVAL_INTERVAL))
        counter += 1
        is_ev = random.random() < config.PROB_EV
        
        if is_ev:
            parking_lot.total_evs += 1
            level = generate_battery_level()
            profile = generate_economic_profile()
            reservation = random.random() < config.PROB_RESERVATION if parking_lot.scheme == AllocationScheme.RESERVATION else False
            env.process(vehicle_quick(env, parking_lot, True, level, profile, reservation))
        else:
            env.process(vehicle_quick(env, parking_lot, False, None, None, False))


def simulate_scenario(scheme, cs_config_name, strategy_name):
    """Run simulation for a specific scenario"""
    random.seed(config.RANDOM_SEED)
    env = simpy.Environment()
    
    # Create config with prices
    base_config = config.CS_CONFIGS_COMPARISON[cs_config_name]
    strategy = config.PRICING_STRATEGIES[strategy_name]
    cs_config = [(name, dist, spots, strategy(dist)) for name, dist, spots in base_config]
    
    parking_lot = ParkingLotComparison(env, cs_config, scheme)
    env.process(vehicle_generator_quick(env, parking_lot))
    env.run(until=config.SIMULATION_TIME)
    
    return parking_lot


def compare_schemes():
    """Compare only the 4 allocation schemes"""
    print("=" * 100)
    print("COMPARISON: Allocation Schemes")
    print("=" * 100)
    
    results = {}
    for scheme in AllocationScheme:
        print(f"🔄 {scheme.value.upper()}...", end=" ")
        parking = simulate_scenario(scheme, "Near", "Competitive")
        results[scheme.value] = parking
        print(f"✓")
    
    print(f"\n{'Scheme':<15} {'EVs→CS':<10} {'EV Wait':<12} {'Revenue':<12}")
    print("-" * 100)
    for name, parking in results.items():
        evs_cs = sum(cs.vehicles_served for cs in parking.charging_stations)
        wait = parking.ev_wait_time / parking.num_ev_waits if parking.num_ev_waits > 0 else 0
        print(f"{name:<15} {evs_cs:<10} {wait:<12.2f} ${parking.total_revenue:<10.2f}")


def compare_pricing_strategies():
    """Compare pricing strategies"""
    print("\n" + "=" * 100)
    print("COMPARISON: Pricing Strategies")
    print("=" * 100)
    
    results = {}
    for strategy in config.PRICING_STRATEGIES.keys():
        print(f"🔄 {strategy}...", end=" ")
        parking = simulate_scenario(AllocationScheme.EXCLUSIVE, "Mixed", strategy)
        results[strategy] = parking
        print(f"✓")
    
    print(f"\n{'Strategy':<15} {'EVs→CS':<10} {'Revenue':<12} {'Popular CS':<20}")
    print("-" * 100)
    for name, parking in results.items():
        evs_cs = sum(cs.vehicles_served for cs in parking.charging_stations)
        popular = max(parking.charging_stations, key=lambda cs: cs.vehicles_served).name
        print(f"{name:<15} {evs_cs:<10} ${parking.total_revenue:<10.2f} {popular:<20}")


def compare_global_top10():
    """Global comparison - TOP 10 best combinations"""
    print("\n" + "=" * 100)
    print("GLOBAL COMPARISON: TOP 10 Best Combinations")
    print("=" * 100)
    
    results = []
    schemes = [AllocationScheme.ON_DEMAND, AllocationScheme.EXCLUSIVE, AllocationScheme.PRIORITY]
    total = len(schemes) * len(config.CS_CONFIGS_COMPARISON) * len(config.PRICING_STRATEGIES)
    counter = 0
    
    for scheme in schemes:
        for cs_config_name in config.CS_CONFIGS_COMPARISON.keys():
            for strategy in config.PRICING_STRATEGIES.keys():
                counter += 1
                print(f"\r🔄 Simulating [{counter}/{total}]...", end="", flush=True)
                parking = simulate_scenario(scheme, cs_config_name, strategy)
                results.append({
                    'scheme': scheme.value,
                    'config': cs_config_name,
                    'strategy': strategy,
                    'parking': parking
                })
    
    print(" ✓\n")
    
    # Ranking by revenue
    ranking = sorted(results, key=lambda x: x['parking'].total_revenue, reverse=True)
    
    print(f"\n{'#':<4} {'Scheme':<12} {'CS Config':<14} {'Strategy':<12} {'Revenue':<12} {'EVs→CS':<8}")
    print("-" * 100)
    
    for i, r in enumerate(ranking[:10], 1):
        parking = r['parking']
        evs_cs = sum(cs.vehicles_served for cs in parking.charging_stations)
        print(f"{i:<4} {r['scheme']:<12} {r['config']:<14} {r['strategy']:<12} "
              f"${parking.total_revenue:<10.2f} {evs_cs:<8}")
    
    # Best combination
    print("\n" + "=" * 100)
    best = ranking[0]
    parking = best['parking']
    evs_cs = sum(cs.vehicles_served for cs in parking.charging_stations)
    
    print(f"🏆 BEST: {best['scheme'].upper()} × {best['config']} × {best['strategy']}")
    print(f"   Revenue: ${parking.total_revenue:.2f} | EVs at CS: {evs_cs}/{parking.total_evs}")


def main():
    """Main menu"""
    print("\n" + "=" * 100)
    print("E-MOBILITY COMPARATOR - Scenario Analysis")
    print("=" * 100)
    print("\nComparison Modes:")
    print("  1. Compare Allocation Schemes (4 simulations)")
    print("  2. Compare Pricing Strategies (3 simulations)")
    print("  3. Global Comparison - TOP 10 (27 simulations)")
    print("\nRunning ALL...\n")
    
    compare_schemes()
    compare_pricing_strategies()
    compare_global_top10()
    
    print("\n" + "=" * 100)
    print("✅ Complete analysis! See docs/ for more details.")
    print("=" * 100)


if __name__ == '__main__':
    main()

