"""
COMPARADOR DE LUCRO - Maximizar Revenue

Foca em encontrar as configurações que maximizam o lucro total.
Compara diferentes combinações de:
- Allocation Schemes
- Charging Station Configurations
- Pricing Strategies
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


def compare_maximize_revenue():
    """Comparação focada em MAXIMIZAR LUCRO"""
    print("\n" + "=" * 100)
    print("COMPARAÇÃO: MAXIMIZAR LUCRO (Revenue)")
    print("=" * 100)
    
    results = []
    schemes = [AllocationScheme.ON_DEMAND, AllocationScheme.RESERVATION]
    total = len(schemes) * len(config.CS_CONFIGS_COMPARISON) * len(config.PRICING_STRATEGIES)
    counter = 0
    
    for scheme in schemes:
        for cs_config_name in config.CS_CONFIGS_COMPARISON.keys():
            for strategy in config.PRICING_STRATEGIES.keys():
                counter += 1
                print(f"\r🔄 Simulando [{counter}/{total}]...", end="", flush=True)
                parking = simulate_scenario(scheme, cs_config_name, strategy)
                
                # Calcular métricas de revenue
                time_hours = config.SIMULATION_TIME / 60.0
                revenue_per_hour = parking.total_revenue / time_hours if time_hours > 0 else 0
                ev_revenue_ratio = parking.ev_revenue / parking.total_revenue if parking.total_revenue > 0 else 0
                
                results.append({
                    'scheme': scheme.value,
                    'config': cs_config_name,
                    'strategy': strategy,
                    'parking': parking,
                    'revenue': parking.total_revenue,
                    'revenue_per_hour': revenue_per_hour,
                    'ev_revenue_ratio': ev_revenue_ratio
                })
    
    print(" ✓\n")
    
    # Ranking por revenue total (métrica principal)
    ranking = sorted(results, key=lambda x: x['revenue'], reverse=True)
    
    print(f"\n{'#':<4} {'Scheme':<12} {'CS Config':<14} {'Strategy':<12} {'Revenue':<12} {'$/h':<10} {'EV %':<8}")
    print("-" * 100)
    
    for i, r in enumerate(ranking[:10], 1):
        parking = r['parking']
        print(f"{i:<4} {r['scheme']:<12} {r['config']:<14} {r['strategy']:<12} "
              f"${r['revenue']:<10.2f} ${r['revenue_per_hour']:<9.2f} {r['ev_revenue_ratio']*100:<7.1f}%")
    
    # Melhor combinação
    print("\n" + "=" * 100)
    best = ranking[0]
    parking = best['parking']
    evs_cs = sum(cs.vehicles_served for cs in parking.charging_stations)
    adoption = (evs_cs / parking.total_evs * 100) if parking.total_evs > 0 else 0
    
    print(f"🏆 MELHOR PARA LUCRO: {best['scheme'].upper()} × {best['config']} × {best['strategy']}")
    print(f"   💰 Revenue Total: ${best['revenue']:.2f}")
    print(f"   💵 Revenue/Hora: ${best['revenue_per_hour']:.2f}")
    print(f"   🔋 Revenue de EVs: ${parking.ev_revenue:.2f} ({best['ev_revenue_ratio']*100:.1f}%)")
    print(f"   📊 EVs em CS: {evs_cs}/{parking.total_evs} ({adoption:.1f}%)")
    
    return ranking


def main():
    """Main function"""
    print("\n" + "=" * 100)
    print("E-MOBILITY COMPARATOR - MAXIMIZAR LUCRO")
    print("=" * 100)
    print("\nAnalisando todas as combinações para encontrar a configuração")
    print("que maximiza o lucro total...\n")
    
    ranking = compare_maximize_revenue()
    
    print("\n" + "=" * 100)
    print("✅ Análise completa! Use comparator_cs_usage.py para análise de uso de CS.")
    print("=" * 100)


if __name__ == '__main__':
    main()

