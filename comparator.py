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
        for i, (name, distance, num_spots, charging_speed_kw, price_per_kwh) in enumerate(cs_config):
            cs = ChargingStation(
                id=i, name=name, distance_from_entrance=distance,
                num_spots=num_spots,
                charging_speed_kw=charging_speed_kw,
                price_per_kwh=price_per_kwh,
                parking_price_per_hour=config.CHARGING_STATION_PARKING_PRICE,
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
    
    # Create config with prices (strategy returns (charging_speed_kw, price_per_kwh))
    base_config = config.CS_CONFIGS_COMPARISON[cs_config_name]
    strategy = config.PRICING_STRATEGIES[strategy_name]
    cs_config = [(name, dist, spots, *strategy(dist)) for name, dist, spots in base_config]
    
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
        parking = simulate_scenario(AllocationScheme.ON_DEMAND, "Mixed", strategy)
        results[strategy] = parking
        print(f"✓")
    
    print(f"\n{'Strategy':<15} {'EVs→CS':<10} {'Revenue':<12} {'Popular CS':<20}")
    print("-" * 100)
    for name, parking in results.items():
        evs_cs = sum(cs.vehicles_served for cs in parking.charging_stations)
        popular = max(parking.charging_stations, key=lambda cs: cs.vehicles_served).name
        print(f"{name:<15} {evs_cs:<10} ${parking.total_revenue:<10.2f} {popular:<20}")


def main():
    """Main menu - Comparações básicas"""
    print("\n" + "=" * 100)
    print("E-MOBILITY COMPARATOR - Análise de Cenários")
    print("=" * 100)
    print("\nComparações Básicas:")
    print("  1. Comparar Esquemas de Alocação")
    print("  2. Comparar Estratégias de Preço")
    print("\nPara análises específicas, use:")
    print("  • comparator_revenue.py - Maximizar Lucro")
    print("  • comparator_cs_usage.py - Maximizar Uso de CS")
    print("\nExecutando comparações básicas...\n")
    
    compare_schemes()
    compare_pricing_strategies()
    
    print("\n" + "=" * 100)
    print("✅ Análise básica completa!")
    print("   Use comparator_revenue.py ou comparator_cs_usage.py para análises específicas.")
    print("=" * 100)


if __name__ == '__main__':
    main()

