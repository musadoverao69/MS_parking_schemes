# 🏗️ Entities and Properties - System Model

Complete documentation of all entities (classes) and their properties in the simulation system.

---

## 📋 Overview

The simulation system models **4 main entities**:

1. **ChargingStation** - Physical charging station in the parking lot
2. **ParkingLot** - The complete parking system
3. **Vehicle** - Vehicle arriving at parking lot (implicit entity)
4. **Enumerations** - Types and categories (AllocationScheme, BatteryLevel, EconomicProfile)

---

## 🔌 ENTITY 1: ChargingStation

**File:** `models/charging_station.py`  
**Type:** `@dataclass`  
**Description:** Represents a physical charging station with specific location and pricing

### Properties (Attributes)

#### Identification Properties

| Property | Type | Description | Example |
|----------|------|-------------|---------|
| `id` | int | Unique identifier | 0, 1, 2 |
| `name` | str | Station name | "CS-Near", "CS-Main" |

#### Physical Properties

| Property | Type | Description | Example | Unit |
|----------|------|-------------|---------|------|
| `distance_from_entrance` | float | Distance from mall entrance | 30.0, 80.0, 150.0 | meters |
| `num_spots` | int | Number of parking spots | 3, 4, 5 | spots |

#### Economic Properties

| Property | Type | Description | Example | Unit |
|----------|------|-------------|---------|------|
| `price_per_hour` | float | Charging price | 12.0, 8.0, 6.0 | $/hour |

#### SimPy Resources

| Property | Type | Description | Usage |
|----------|------|-------------|-------|
| `resource` | simpy.Resource | Queue management | Regular schemes |
| `resource_priority` | simpy.PriorityResource | Priority queue | RESERVATION scheme |

#### Statistics (Collected During Simulation)

| Property | Type | Description | Initial Value | Unit |
|----------|------|-------------|---------------|------|
| `vehicles_served` | int | Total vehicles served | 0 | count |
| `total_usage_time` | float | Total time spots were occupied | 0.0 | minutes |
| `total_revenue` | float | Total revenue generated | 0.0 | $ |
| `distance_rejections` | int | Rejections due to distance | 0 | count |
| `price_rejections` | int | Rejections due to price | 0 | count |

### Example

```python
cs = ChargingStation(
    id=1,
    name="CS-Near",
    distance_from_entrance=30.0,
    num_spots=5,
    price_per_hour=12.0,
    resource=simpy.Resource(env, capacity=5),
    resource_priority=None,
    vehicles_served=0,
    total_usage_time=0.0,
    total_revenue=0.0,
    distance_rejections=0,
    price_rejections=0
)
```

### Calculated Metrics

From ChargingStation properties, we calculate:

| Metric | Formula | Unit |
|--------|---------|------|
| **Utilization Rate** | `(total_usage_time / (SIMULATION_TIME × num_spots)) × 100` | % |
| **Average Usage Time** | `total_usage_time / vehicles_served` | min |
| **Revenue per Vehicle** | `total_revenue / vehicles_served` | $ |
| **Rejection Rate** | `(distance_rej + price_rej) / total_evs × 100` | % |

---

## 🅿️ ENTITY 2: ParkingLot

**File:** `simulator.py`  
**Type:** `class ParkingLot`  
**Description:** The complete parking lot system with regular spots and charging stations

### Properties (Attributes)

#### System Configuration

| Property | Type | Description | Example |
|----------|------|-------------|---------|
| `env` | simpy.Environment | Simulation environment | - |
| `scheme` | AllocationScheme | Allocation scheme used | EXCLUSIVE, ON_DEMAND |

#### Resources

| Property | Type | Description | Capacity |
|----------|------|-------------|----------|
| `regular_spots` | simpy.Resource | Regular parking spots | 50 (config) |
| `charging_stations` | List[ChargingStation] | List of CS | 3-10 stations |

#### Pricing

| Property | Type | Description | Example | Unit |
|----------|------|-------------|---------|------|
| `regular_price` | float | Regular spot price | 5.0 | $/hour |

#### Derived Properties

| Property | Type | Formula | Description |
|----------|------|---------|-------------|
| `total_ev_spots` | int | `sum(cs.num_spots)` | Total EV spots available |

#### Vehicle Statistics

| Property | Type | Description | Initial | Unit |
|----------|------|-------------|---------|------|
| `total_vehicles` | int | Total vehicles arrived | 0 | count |
| `total_evs` | int | Total EVs arrived | 0 | count |
| `vehicles_served` | int | Vehicles parked successfully | 0 | count |
| `evs_served` | int | EVs parked successfully | 0 | count |

#### Time Statistics

| Property | Type | Description | Initial | Unit |
|----------|------|-------------|---------|------|
| `total_wait_time` | float | Sum of all wait times | 0.0 | minutes |
| `ev_wait_time` | float | Sum of EV wait times | 0.0 | minutes |
| `regular_wait_time` | float | Sum of regular wait times | 0.0 | minutes |
| `num_ev_waits` | int | Count of EVs that waited | 0 | count |
| `num_regular_waits` | int | Count of regulars that waited | 0 | count |

#### Decision Statistics

| Property | Type | Description | Initial | Unit |
|----------|------|-------------|---------|------|
| `evs_chose_regular_distance` | int | EVs chose regular due to distance | 0 | count |
| `evs_chose_regular_battery_ok` | int | EVs chose regular (battery OK) | 0 | count |
| `evs_chose_regular_price` | int | EVs chose regular due to price | 0 | count |
| `regular_used_ev` | int | Regular cars used EV spots | 0 | count |

#### Financial Statistics

| Property | Type | Description | Initial | Unit |
|----------|------|-------------|---------|------|
| `total_revenue` | float | Total revenue | 0.0 | $ |
| `regular_revenue` | float | Revenue from regular spots | 0.0 | $ |
| `ev_revenue` | float | Revenue from CS spots | 0.0 | $ |

### Example

```python
parking_lot = ParkingLot(env, AllocationScheme.EXCLUSIVE)
# Has all properties initialized
# charging_stations loaded from config
# All statistics start at 0
```

---

## 🚗 ENTITY 3: Vehicle (Implicit)

**Description:** Vehicles are not stored as objects but represented as processes  
**Represented by:** `vehicle_process()` generator function  
**Lifecycle:** Arrival → Decision → Waiting → Parking → Departure

### Properties (Process Parameters)

| Property | Type | Description | Values | Required For |
|----------|------|-------------|--------|--------------|
| `name` | str | Vehicle identifier | "V-1", "V-2", ... | All |
| `is_ev` | bool | Is electric vehicle | True/False | All |
| `battery_level` | BatteryLevel | Battery state | CRITICAL/LOW/MEDIUM/HIGH | EVs only |
| `economic_profile` | EconomicProfile | Price sensitivity | BUDGET/MODERATE/PREMIUM | EVs only |
| `has_reservation` | bool | Has reservation | True/False | RESERVATION scheme |

### Derived Properties (Calculated)

| Property | Type | Calculation | Description |
|----------|------|-------------|-------------|
| `arrival_time` | float | `env.now` at arrival | Time vehicle arrived |
| `wait_time` | float | `parking_time - arrival_time` | Time waited in queue |
| `parking_duration` | int | `random.randint(30, 120)` | Time parked (min) |
| `cost` | float | `(duration/60) × price` | Total parking cost |
| `chosen_spot_type` | str | Based on decision logic | "Regular", "CS-Near", etc |
| `chosen_price` | float | Based on spot type | 5.0, 8.0, 12.0 |

### Vehicle Behavior (State Machine)

```
State 1: ARRIVAL
  ├─ Generate properties (battery, profile)
  ├─ Record arrival time
  └─ Enter decision phase

State 2: DECISION
  ├─ Evaluate battery level
  ├─ Check distance tolerance
  ├─ Check price tolerance
  ├─ Choose spot type
  └─ Enter waiting phase

State 3: WAITING
  ├─ Request resource (spot)
  ├─ Wait if no spot available
  ├─ Record wait time
  └─ Enter parking phase

State 4: PARKING
  ├─ Occupy spot
  ├─ Generate parking duration
  ├─ Wait (timeout)
  └─ Enter departure phase

State 5: DEPARTURE
  ├─ Calculate cost
  ├─ Update statistics
  ├─ Release resource
  └─ Exit system
```

---

## 📊 ENTITY 4: Enumerations (Types)

### 4.1 AllocationScheme

**File:** `models/enums.py`  
**Type:** `Enum`  
**Description:** Parking allocation strategy

#### Values

| Value | String | Description | Behavior |
|-------|--------|-------------|----------|
| `ON_DEMAND` | "on_demand" | EVs try CS, can use regular | Flexible |
| `EXCLUSIVE` | "exclusive" | CS exclusive for EVs | Strict |
| `PRIORITY` | "priority" | EVs priority, regulars can use empty CS | Optimized |
| `RESERVATION` | "reservation" | Advance reservation system | Planned |

**Usage:**
```python
from models import AllocationScheme
scheme = AllocationScheme.EXCLUSIVE
```

---

### 4.2 BatteryLevel

**File:** `models/enums.py`  
**Type:** `Enum`  
**Description:** EV battery state

#### Values

| Value | String | Battery % | Probability | Behavior |
|-------|--------|-----------|-------------|----------|
| `CRITICAL` | "critical" | < 20% | 15% | MUST charge - accepts any distance/price |
| `LOW` | "low" | 20-40% | 20% | Prefers charging - up to 120m, 2× price |
| `MEDIUM` | "medium" | 40-70% | 35% | Flexible - up to 80m, 1.5× price |
| `HIGH` | "high" | > 70% | 30% | Doesn't need - up to 50m, 1.2× price |

**Properties per Level:**

| Level | Max Distance | Max Price Tolerance | Decision Priority |
|-------|--------------|---------------------|-------------------|
| CRITICAL | 200m | 300% (3×) | Charging > All |
| LOW | 120m | 200% (2×) | Charging > Convenience |
| MEDIUM | 80m | 150% (1.5×) | Balanced |
| HIGH | 50m | 120% (1.2×) | Convenience > Charging |

**Usage:**
```python
from models import BatteryLevel, generate_battery_level
level = generate_battery_level()  # Random generation
if level == BatteryLevel.CRITICAL:
    print("Must charge urgently!")
```

---

### 4.3 EconomicProfile

**File:** `models/enums.py`  
**Type:** `Enum`  
**Description:** Driver price sensitivity

#### Values

| Value | String | Probability | Price Tolerance Multiplier | Behavior |
|-------|--------|-------------|---------------------------|----------|
| `BUDGET` | "budget" | 30% | 0.8× (reduces 20%) | Very price sensitive |
| `MODERATE` | "moderate" | 50% | 1.0× (maintains) | Average sensitivity |
| `PREMIUM` | "premium" | 20% | 1.5× (increases 50%) | Low sensitivity |

**Effect on Decision:**

Combined with battery level:
```python
# Example: LOW battery + BUDGET profile
max_price = $5.00 × (200% × 0.8) / 100 = $8.00

# Example: LOW battery + PREMIUM profile  
max_price = $5.00 × (200% × 1.5) / 100 = $15.00
```

**Usage:**
```python
from models import EconomicProfile, generate_economic_profile
profile = generate_economic_profile()  # Random generation
```

---

## 🔗 ENTITY RELATIONSHIPS

```
ParkingLot (1)
├── has many → ChargingStation (0..N)
│   ├── has → resource (SimPy Resource)
│   └── serves many → Vehicle (0..N)
│
├── has → regular_spots (SimPy Resource)
│   └── serves many → Vehicle (0..N)
│
└── receives many → Vehicle (0..N)
    ├── has → battery_level (if EV)
    ├── has → economic_profile (if EV)
    ├── chooses → ChargingStation OR regular_spot
    └── generates → Statistics
```

---

## 📊 COMPLETE ENTITY DIAGRAM

```
┌─────────────────────────────────────────────────────────────┐
│ ParkingLot                                                  │
├─────────────────────────────────────────────────────────────┤
│ Configuration:                                              │
│  • env: Environment                                         │
│  • scheme: AllocationScheme                                 │
│  • regular_spots: Resource                                  │
│  • regular_price: float                                     │
│  • charging_stations: List[ChargingStation]                 │
│  • total_ev_spots: int                                      │
│                                                              │
│ Vehicle Statistics:                                         │
│  • total_vehicles: int                                      │
│  • total_evs: int                                           │
│  • vehicles_served: int                                     │
│  • evs_served: int                                          │
│                                                              │
│ Time Statistics:                                            │
│  • total_wait_time: float                                   │
│  • ev_wait_time: float                                      │
│  • regular_wait_time: float                                 │
│  • num_ev_waits: int                                        │
│  • num_regular_waits: int                                   │
│                                                              │
│ Decision Statistics:                                        │
│  • evs_chose_regular_distance: int                          │
│  • evs_chose_regular_battery_ok: int                        │
│  • evs_chose_regular_price: int                             │
│  • regular_used_ev: int                                     │
│                                                              │
│ Financial Statistics:                                       │
│  • total_revenue: float                                     │
│  • regular_revenue: float                                   │
│  • ev_revenue: float                                        │
└─────────────────────────────────────────────────────────────┘
                    │
                    │ has many
                    ▼
┌─────────────────────────────────────────────────────────────┐
│ ChargingStation                                             │
├─────────────────────────────────────────────────────────────┤
│ Identification:                                             │
│  • id: int                                                  │
│  • name: str                                                │
│                                                              │
│ Physical:                                                   │
│  • distance_from_entrance: float                            │
│  • num_spots: int                                           │
│                                                              │
│ Economic:                                                   │
│  • price_per_hour: float                                    │
│                                                              │
│ Resources:                                                  │
│  • resource: Resource                                       │
│  • resource_priority: PriorityResource                      │
│                                                              │
│ Statistics:                                                 │
│  • vehicles_served: int                                     │
│  • total_usage_time: float                                  │
│  • total_revenue: float                                     │
│  • distance_rejections: int                                 │
│  • price_rejections: int                                    │
└─────────────────────────────────────────────────────────────┘
                    │
                    │ serves
                    ▼
┌─────────────────────────────────────────────────────────────┐
│ Vehicle (Process)                                           │
├─────────────────────────────────────────────────────────────┤
│ Identification:                                             │
│  • name: str                                                │
│  • is_ev: bool                                              │
│                                                              │
│ EV Properties (if is_ev):                                   │
│  • battery_level: BatteryLevel                              │
│  • economic_profile: EconomicProfile                        │
│  • has_reservation: bool                                    │
│                                                              │
│ Process Variables:                                          │
│  • arrival_time: float                                      │
│  • wait_time: float                                         │
│  • parking_duration: int                                    │
│  • chosen_spot: Resource                                    │
│  • chosen_price: float                                      │
│  • cost: float                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 PROPERTY TYPES SUMMARY

### Static Properties
**Set at initialization, don't change:**
- ChargingStation: id, name, distance, num_spots, price
- ParkingLot: env, scheme, regular_price, num_spots

### Dynamic Properties (Resources)
**Change during simulation:**
- resource.count (current occupancy)
- resource.queue (vehicles waiting)

### Accumulator Properties
**Increment during simulation:**
- vehicles_served
- total_usage_time
- total_revenue
- total_wait_time
- rejections

---

## 📐 DATA TYPES USED

| Type | Usage | Examples |
|------|-------|----------|
| `int` | Counters, IDs, spots | vehicles_served, id, num_spots |
| `float` | Times, prices, distances | wait_time, price_per_hour, distance |
| `str` | Names, identifiers | name, "V-1", "CS-Near" |
| `bool` | Flags | is_ev, has_reservation |
| `Enum` | Categories | AllocationScheme, BatteryLevel |
| `simpy.Resource` | Queue management | resource, regular_spots |
| `simpy.PriorityResource` | Priority queues | resource_priority |
| `List[ChargingStation]` | Collections | charging_stations |

---

## 🔄 PROPERTY LIFECYCLE

### ChargingStation Properties

```
INITIALIZATION:
  ├─ id, name, distance, num_spots, price ──► Set from config
  ├─ resource ──────────────────────────────► Created from env
  ├─ vehicles_served ───────────────────────► 0
  └─ total_usage_time ──────────────────────► 0.0

DURING SIMULATION:
  ├─ resource.count ────────────────────────► Changes (0 to num_spots)
  ├─ vehicles_served ───────────────────────► Increments (+1 per vehicle)
  ├─ total_usage_time ──────────────────────► Increments (+duration)
  ├─ total_revenue ─────────────────────────► Increments (+cost)
  ├─ distance_rejections ───────────────────► Increments (if rejected)
  └─ price_rejections ──────────────────────► Increments (if rejected)

END OF SIMULATION:
  ├─ All accumulators have final values
  ├─ Calculate: utilization_rate, avg_usage, revenue_per_vehicle
  └─ Generate reports
```

### Vehicle Process Lifecycle

```
CREATION:
  ├─ Generate: is_ev (random)
  ├─ If EV: generate battery_level, economic_profile
  ├─ If RESERVATION: generate has_reservation
  └─ Record: arrival_time

DECISION PHASE:
  ├─ Evaluate: battery_level → max_distance, max_price
  ├─ Evaluate: economic_profile → price_tolerance_multiplier
  ├─ Choose: best_cs = choose_charging_station()
  └─ Decide: spot = cs.resource OR regular_spots

WAITING PHASE:
  ├─ Request: spot.request()
  ├─ Wait: until spot available
  ├─ Calculate: wait_time = now - arrival
  └─ Update: parking_lot.wait_time statistics

PARKING PHASE:
  ├─ Generate: parking_duration (random 30-120 min)
  ├─ Timeout: env.timeout(parking_duration)
  └─ Occupy: spot.resource

DEPARTURE PHASE:
  ├─ Calculate: cost = (duration/60) × price
  ├─ Update: cs.vehicles_served, cs.total_usage_time, cs.total_revenue
  ├─ Update: parking_lot statistics
  └─ Release: spot.resource
```

---

## 🔍 PROPERTY ACCESS PATTERNS

### Read Properties (Configuration)

```python
# From config.py
NUM_REGULAR_SPOTS           # Number of regular spots
SIMULATION_TIME             # Simulation duration
PROB_EV                     # EV probability
CHARGING_STATIONS_CONFIG    # CS configuration list
ALLOCATION_SCHEME           # Scheme to use
```

### Write Properties (Statistics)

```python
# During simulation (write)
parking_lot.total_vehicles += 1
parking_lot.evs_served += 1
cs.vehicles_served += 1
cs.total_revenue += cost

# After simulation (read)
print(parking_lot.total_revenue)
print(cs.vehicles_served)
```

---

## 📊 PROPERTY DEPENDENCIES

### Dependent Properties

Some properties depend on others:

```python
# total_ev_spots depends on charging_stations
total_ev_spots = sum(cs.num_spots for cs in charging_stations)

# avg_wait_time depends on total_wait_time and vehicles_served
avg_wait_time = total_wait_time / vehicles_served

# utilization_rate depends on total_usage_time, SIMULATION_TIME, num_spots
utilization = (total_usage_time / (SIMULATION_TIME × num_spots)) × 100

# adoption_rate depends on vehicles_served and total_evs
adoption = (sum(cs.vehicles_served) / total_evs) × 100
```

---

## 🎓 ENTITY SUMMARY TABLE

| Entity | Properties | Key Attributes | Calculated Metrics |
|--------|------------|----------------|-------------------|
| **ChargingStation** | 14 | id, name, distance, price, num_spots | utilization, revenue/vehicle |
| **ParkingLot** | 25+ | scheme, resources, all statistics | avg_wait, revenue/hour |
| **Vehicle** | 8 | is_ev, battery, profile, times | wait_time, cost |
| **Enums** | 3 types | 11 values total | - |

---

## 🔢 TOTAL COUNT

### Properties by Category

- **Identification:** 3 (id, name, vehicle_name)
- **Physical/Spatial:** 2 (distance, num_spots)
- **Economic:** 2 (price, cost)
- **Temporal:** 8 (arrival, wait, duration, usage times)
- **Boolean Flags:** 2 (is_ev, has_reservation)
- **Enumerations:** 3 (scheme, battery, profile)
- **Statistics (counters):** 15+
- **Resources:** 3 (regular_spots, resource, resource_priority)

**TOTAL: 35+ distinct properties** across all entities

---

## 📖 How to Use This Document

### For Understanding the Model

1. Read entity descriptions
2. Understand property types
3. See relationships
4. Check lifecycle

### For Development

1. Check property names
2. Understand data types
3. See formulas
4. Use correct access patterns

### For Analysis

1. Identify which metrics to track
2. Understand what they measure
3. Know how to interpret
4. Use for comparisons

---

## ✅ Complete Entity Model

The simulation implements a **rich entity model** with:

- ✅ **4 main entities** (3 explicit, 1 implicit)
- ✅ **35+ properties** total
- ✅ **30+ metrics** collected
- ✅ **Clear relationships** between entities
- ✅ **Well-defined lifecycles**
- ✅ **Type-safe** with Enums
- ✅ **Comprehensive** statistics

This allows for **complete analysis** of parking lot behavior under different conditions!

---

**Document:** ENTITIES.md  
**Version:** 1.0  
**Date:** October 2025

