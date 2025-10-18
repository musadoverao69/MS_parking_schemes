# 📊 Metrics and Indicators - E-Mobility Parking Simulation

Complete documentation of all metrics and indicators implemented in the project.

---

## 📋 Categories of Metrics

The project collects metrics in **5 main categories**:

1. 📊 **Vehicle Metrics** - Traffic and demand
2. ⏱️ **Time Metrics** - Wait times and efficiency
3. 🅿️ **Utilization Metrics** - Resource usage
4. 💰 **Financial Metrics** - Revenue and profitability
5. 🚗 **Decision Metrics** - User behavior and choices

---

## 1. 📊 VEHICLE METRICS

### 1.1 Total Vehicles
**Variable:** `total_vehicles`  
**Description:** Total number of vehicles that arrived at the parking lot  
**Type:** Counter  
**Usage:** Measure overall demand

### 1.2 Total EVs
**Variable:** `total_evs`  
**Description:** Total number of electric vehicles  
**Type:** Counter  
**Formula:** `count(vehicle.is_ev == True)`  
**Usage:** Measure EV penetration in the parking lot

### 1.3 Vehicles Served
**Variable:** `vehicles_served`  
**Description:** Total vehicles that successfully parked  
**Type:** Counter  
**Usage:** Measure service capacity

### 1.4 EVs Served
**Variable:** `evs_served`  
**Description:** Electric vehicles that successfully parked  
**Type:** Counter  
**Usage:** Measure EV service success rate

### 1.5 Service Rate
**Formula:** `vehicles_served / total_vehicles × 100`  
**Type:** Percentage  
**Range:** 0-100%  
**Interpretation:**
- **> 95%**: Excellent capacity
- **80-95%**: Good capacity
- **< 80%**: Insufficient capacity

---

## 2. ⏱️ TIME METRICS

### 2.1 Total Wait Time
**Variable:** `total_wait_time`  
**Description:** Sum of all waiting times  
**Type:** Accumulator (minutes)  
**Usage:** Calculate average wait time

### 2.2 EV Wait Time
**Variable:** `ev_wait_time`  
**Description:** Sum of EV waiting times  
**Type:** Accumulator (minutes)  
**Usage:** Measure EV-specific service quality

### 2.3 Regular Wait Time
**Variable:** `regular_wait_time`  
**Description:** Sum of regular vehicle waiting times  
**Type:** Accumulator (minutes)  
**Usage:** Measure regular vehicle service quality

### 2.4 Number of EV Waits
**Variable:** `num_ev_waits`  
**Description:** Count of EVs that had to wait  
**Type:** Counter  
**Usage:** Calculate average EV wait time

### 2.5 Average Wait Time (General)
**Formula:** `total_wait_time / vehicles_served`  
**Type:** Average (minutes)  
**Interpretation:**
- **< 5 min**: Excellent
- **5-15 min**: Good
- **15-30 min**: Acceptable
- **> 30 min**: Problematic

### 2.6 Average EV Wait Time
**Formula:** `ev_wait_time / num_ev_waits`  
**Type:** Average (minutes)  
**Interpretation:** Same as general wait time  
**Importance:** Critical for EV user satisfaction

### 2.7 Average Regular Wait Time
**Formula:** `regular_wait_time / num_regular_waits`  
**Type:** Average (minutes)  
**Usage:** Compare fairness between vehicle types

---

## 3. 🅿️ UTILIZATION METRICS

### 3.1 Regular Spot Utilization (Snapshot)
**Formula:** `regular_spots.count / regular_spots.capacity × 100`  
**Type:** Percentage (at end of simulation)  
**Range:** 0-100%  
**Interpretation:**
- **< 50%**: Under-utilized
- **50-80%**: Ideal
- **80-95%**: High utilization
- **> 95%**: Near saturation

### 3.2 Charging Station Utilization (Time-based)
**Formula:** `(total_usage_time / (SIMULATION_TIME × num_spots)) × 100`  
**Type:** Percentage  
**Description:** Percentage of time CS spots were occupied  
**Per CS:** Each charging station has individual metric  
**Interpretation:**
- **< 30%**: Underutilized (consider reducing)
- **30-60%**: Moderate
- **60-80%**: Good utilization
- **> 80%**: High demand (consider expanding)

### 3.3 Total EV Spots
**Variable:** `total_ev_spots`  
**Formula:** `sum(cs.num_spots for all CS)`  
**Type:** Constant  
**Usage:** Compare against demand

### 3.4 CS Occupancy Rate
**Per CS:** `cs.resource.count / cs.num_spots`  
**Type:** Percentage (real-time)  
**Usage:** Monitor current load

---

## 4. 💰 FINANCIAL METRICS

### 4.1 Total Revenue
**Variable:** `total_revenue`  
**Description:** Total revenue generated during simulation  
**Type:** Currency ($)  
**Formula:** `sum(parking_duration/60 × price_per_hour)`  
**Usage:** Overall profitability measure

### 4.2 Regular Spot Revenue
**Variable:** `regular_revenue`  
**Description:** Revenue from regular parking spots  
**Type:** Currency ($)  
**Usage:** Compare revenue sources

### 4.3 EV Spot Revenue
**Variable:** `ev_revenue`  
**Description:** Revenue from charging station spots  
**Type:** Currency ($)  
**Usage:** Measure CS profitability

### 4.4 Revenue per Hour
**Formula:** `total_revenue / (SIMULATION_TIME / 60)`  
**Type:** Currency ($/hour)  
**Usage:** Standardize revenue across different simulation times

### 4.5 Revenue per Vehicle
**Formula:** `total_revenue / vehicles_served`  
**Type:** Currency ($ per vehicle)  
**Usage:** Measure average customer value

### 4.6 CS Revenue Contribution
**Formula:** `ev_revenue / total_revenue × 100`  
**Type:** Percentage  
**Interpretation:**
- Shows how much CS contribute to total revenue
- Higher % = CS are financially important

### 4.7 Revenue per CS
**Variable:** `cs.total_revenue` (per charging station)  
**Type:** Currency ($)  
**Usage:** Compare profitability of different CS locations

### 4.8 Average Revenue per Vehicle (CS)
**Formula:** `cs.total_revenue / cs.vehicles_served`  
**Type:** Currency ($ per vehicle)  
**Usage:** Measure value per customer at each CS

---

## 5. 🚗 DECISION METRICS

### 5.1 EVs at Charging Stations
**Formula:** `sum(cs.vehicles_served)`  
**Type:** Counter  
**Usage:** Measure CS attractiveness

### 5.2 Percentage of EVs Using CS
**Formula:** `(EVs at CS / total_evs) × 100`  
**Type:** Percentage  
**Interpretation:**
- **> 80%**: CS are attractive
- **60-80%**: Moderate attraction
- **< 60%**: CS underutilized (check price/distance)

### 5.3 EVs Choosing Regular Spots (by Battery)
**Variable:** `evs_chose_regular_battery_ok`  
**Description:** EVs that chose regular spots because battery is OK  
**Type:** Counter  
**Interpretation:** Indicates preference for convenience over charging

### 5.4 EVs Choosing Regular Spots (by Distance)
**Variable:** `evs_chose_regular_distance`  
**Description:** EVs that rejected CS due to distance  
**Type:** Counter  
**Interpretation:** CS are too far from entrance

### 5.5 EVs Choosing Regular Spots (by Price)
**Variable:** `evs_chose_regular_price`  
**Description:** EVs that rejected CS due to high price  
**Type:** Counter  
**Interpretation:** CS prices are too high

### 5.6 Regular Vehicles Using EV Spots
**Variable:** `regular_used_ev`  
**Description:** Regular vehicles that used CS (in PRIORITY scheme)  
**Type:** Counter  
**Usage:** Measure CS utilization optimization

### 5.7 Distance Rejections per CS
**Variable:** `cs.distance_rejections`  
**Description:** Number of rejections due to distance at each CS  
**Type:** Counter (per CS)  
**Usage:** Identify poorly located CS

### 5.8 Price Rejections per CS
**Variable:** `cs.price_rejections`  
**Description:** Number of rejections due to price at each CS  
**Type:** Counter (per CS)  
**Usage:** Identify overpriced CS

---

## 6. 🔌 CHARGING STATION SPECIFIC METRICS

### 6.1 Vehicles Served per CS
**Variable:** `cs.vehicles_served`  
**Description:** Total vehicles served at this CS  
**Type:** Counter  
**Usage:** Measure CS popularity

### 6.2 Total Usage Time per CS
**Variable:** `cs.total_usage_time`  
**Description:** Total minutes this CS was occupied  
**Type:** Accumulator (minutes)  
**Usage:** Calculate utilization rate

### 6.3 Average Usage Time per CS
**Formula:** `cs.total_usage_time / cs.vehicles_served`  
**Type:** Average (minutes)  
**Usage:** Understand parking duration patterns at each CS

### 6.4 CS Utilization Rate
**Formula:** `(cs.total_usage_time / (SIMULATION_TIME × cs.num_spots)) × 100`  
**Type:** Percentage  
**Interpretation:**
- **> 80%**: High demand
- **50-80%**: Good
- **30-50%**: Moderate
- **< 30%**: Low demand

---

## 📈 COMPARATIVE METRICS

These metrics are used to compare different scenarios:

### 7.1 Scheme Comparison Metrics

**Compared by:**
- Average EV wait time
- % EVs using CS
- Total revenue
- Service rate
- EVs in regular spots

### 7.2 CS Configuration Comparison Metrics

**Compared by:**
- Total EVs served at CS
- Average CS utilization
- Distance rejections
- Revenue per CS
- Most/least popular CS

### 7.3 Pricing Strategy Comparison Metrics

**Compared by:**
- Total revenue
- % EVs using CS
- Price rejections
- Revenue per vehicle
- Most profitable CS

---

## 🎯 KEY PERFORMANCE INDICATORS (KPIs)

### KPI 1: EV Service Quality
**Formula:** `(evs_served / total_evs) × 100`  
**Target:** > 95%  
**Importance:** Critical for EV user satisfaction

### KPI 2: CS Adoption Rate
**Formula:** `(EVs at CS / total_evs) × 100`  
**Target:** > 70%  
**Importance:** Measures CS investment success

### KPI 3: Average EV Wait Time
**Target:** < 10 minutes  
**Importance:** User experience metric

### KPI 4: Revenue per Hour
**Target:** Maximize (compare scenarios)  
**Importance:** Business viability

### KPI 5: CS Utilization Rate
**Target:** 60-80%  
**Importance:** Resource optimization

### KPI 6: Price Rejection Rate
**Formula:** `sum(price_rejections) / total_evs × 100`  
**Target:** < 20%  
**Importance:** Pricing strategy validation

### KPI 7: Distance Rejection Rate
**Formula:** `sum(distance_rejections) / total_evs × 100`  
**Target:** < 15%  
**Importance:** Location strategy validation

---

## 📊 METRICS SUMMARY TABLE

| Category | Metric | Variable/Formula | Unit | Importance |
|----------|--------|------------------|------|------------|
| **Vehicles** | Total EVs | `total_evs` | count | High |
| **Vehicles** | EVs Served | `evs_served` | count | Critical |
| **Vehicles** | Service Rate | `served/total×100` | % | High |
| **Time** | Avg EV Wait | `ev_wait/num_waits` | min | Critical |
| **Time** | Avg Regular Wait | `regular_wait/num_waits` | min | Medium |
| **Utilization** | CS Usage Rate | `usage_time/(time×spots)×100` | % | High |
| **Financial** | Total Revenue | `total_revenue` | $ | High |
| **Financial** | Revenue/Hour | `revenue/(time/60)` | $/h | High |
| **Financial** | CS Revenue % | `ev_revenue/total×100` | % | Medium |
| **Decision** | EVs at CS % | `evs_at_cs/total_evs×100` | % | Critical |
| **Decision** | Price Rejections | `sum(price_rej)` | count | High |
| **Decision** | Distance Rejections | `sum(dist_rej)` | count | High |

---

## 🎓 How Metrics Are Used

### For Scheme Comparison

**Primary metrics:**
1. Average EV wait time (lower is better)
2. % EVs using CS (higher is better for CS investment)
3. Service rate (higher is better)
4. Revenue per hour (higher is better)

**Example output:**
```
Scheme          EVs→CS     EV Wait      Revenue     
on_demand       20         7.74         $551.90    
exclusive       20         7.74         $551.90    
priority        20         7.74         $551.90    
```

### For Pricing Strategy Comparison

**Primary metrics:**
1. Total revenue (higher is better)
2. EVs using CS (balance needed)
3. Price rejections (lower is better)
4. Most popular CS (identify sweet spot)

**Example output:**
```
Strategy        EVs→CS     Revenue      Popular CS          
Premium         12         $541.32      CS-Mid              
Competitive     21         $549.05      CS-Near             
```

### For CS Location Analysis

**Primary metrics:**
1. Vehicles served per CS
2. Utilization rate per CS
3. Distance rejections per CS
4. Revenue per CS

**Example output:**
```
CS-Near (30m, $12.00/h):
  Served: 14 | Usage: 81.6% | Revenue: $235.00
  Rejections: 0 (distance) + 29 (price)
```

---

## 📐 METRIC FORMULAS

### Utilization Rate
```python
utilization_rate = (total_usage_time / (SIMULATION_TIME × num_spots)) × 100
```
**Example:** CS with 5 spots, 480 min simulation, used 1200 minutes total
→ (1200 / (480 × 5)) × 100 = 50% utilization

### Average Wait Time
```python
avg_wait_time = total_wait_time / num_vehicles_waited
```
**Example:** 100 vehicles waited total 500 minutes
→ 500 / 100 = 5 minutes average

### CS Adoption Rate
```python
adoption_rate = (sum(cs.vehicles_served) / total_evs) × 100
```
**Example:** 25 EVs total, 20 used CS
→ (20 / 25) × 100 = 80% adoption

### Revenue per Hour
```python
revenue_per_hour = total_revenue / (SIMULATION_TIME / 60)
```
**Example:** $752.85 revenue in 480 minutes
→ 752.85 / 8 = $94.11 per hour

### Rejection Rate
```python
price_rejection_rate = (sum(price_rejections) / total_evs) × 100
distance_rejection_rate = (sum(distance_rejections) / total_evs) × 100
```

---

## 🎯 DECISION FACTOR METRICS

### Distance Factor

**Metrics:**
- `distance_rejections` - Rejections due to CS being too far
- `evs_chose_regular_distance` - EVs that chose regular due to distance

**Measured per:**
- Individual CS
- Battery level
- Total

**Key insight:** Shows how distance affects user decisions

### Battery Factor

**Metrics:**
- Distribution of battery levels (Critical/Low/Medium/High)
- Decisions by battery level
- `evs_chose_regular_battery_ok` - EVs with good battery chose regular

**Key insight:** Shows urgency affects willingness to walk/pay

### Price Factor

**Metrics:**
- `price_rejections` - Rejections due to high price
- `evs_chose_regular_price` - EVs that chose regular due to price
- Revenue per CS

**Key insight:** Shows price sensitivity and elasticity

---

## 🔬 RESEARCH METRICS

### Economic Analysis Metrics

1. **Return on Investment (ROI)**
   - Not directly implemented but can be calculated:
   - `ROI = (ev_revenue × days_per_year) / installation_cost`

2. **Price Elasticity**
   - Compare % EVs using CS at different prices
   - Formula: `% change in demand / % change in price`

3. **Value of Convenience**
   - Compare revenue at different distances for same price
   - Shows willingness to pay for proximity

### Behavioral Metrics

1. **Battery Level Distribution**
   - 15% Critical, 20% Low, 35% Medium, 30% High
   - Validates realistic user behavior

2. **Economic Profile Distribution**
   - 30% Budget, 50% Moderate, 20% Premium
   - Shows customer segmentation

3. **Decision Trade-offs**
   - Distance vs Price
   - Battery vs Price
   - Battery vs Distance

---

## 📊 OUTPUT METRICS SUMMARY

### Simulator Output

```python
📊 VEHICLES:
  Total: 113 (33 EVs)                    # total_vehicles, total_evs
  Served: 95 (23 EVs)                    # vehicles_served, evs_served

⏱️ WAIT TIMES:
  EVs: 19.20 min                         # ev_wait_time / num_ev_waits
  Regular: 0.00 min                      # regular_wait_time / num_regular_waits

🔌 CHARGING STATIONS:
  CS-Near (30m, $12.00/h):
    Served: 14                           # cs.vehicles_served
    Usage: 81.6%                         # (usage_time / (sim_time × spots)) × 100
    Revenue: $235.00                     # cs.total_revenue
    Rejections: 0 (distance) + 29 (price) # cs.distance_rej, cs.price_rej

💰 FINANCIAL:
  Total revenue: $752.85                 # total_revenue
  Revenue/hour: $94.11                   # total_revenue / (time/60)

🚗 DECISIONS:
  EVs at CS: 23/33 (69.7%)              # sum(cs.served) / total_evs × 100
  EVs at regular: 10                     # evs_chose_regular_*
```

---

## 🎓 Metrics for Academic Analysis

### 1. Service Quality Metrics
- Average wait time
- Service rate
- Queue lengths

### 2. Efficiency Metrics
- Utilization rates
- Spot turnover
- Resource optimization

### 3. Economic Metrics
- Revenue generation
- Price elasticity
- ROI potential

### 4. Behavioral Metrics
- User preferences
- Decision patterns
- Sensitivity analysis

### 5. Comparative Metrics
- Scheme performance
- Location effectiveness
- Pricing strategies

---

## 📈 TREND ANALYSIS (if extended)

### Potential Time-Series Metrics

1. **Utilization over time**
   - Track occupancy every hour
   - Identify peak periods

2. **Revenue over time**
   - Track revenue per hour
   - Optimize pricing by period

3. **Queue length over time**
   - Identify congestion periods
   - Optimize capacity

---

## ✅ COMPLETE METRICS LIST

### Collected Automatically

**Vehicle Metrics (5):**
- total_vehicles
- total_evs
- vehicles_served
- evs_served
- Service rate (calculated)

**Time Metrics (7):**
- total_wait_time
- ev_wait_time
- regular_wait_time
- num_ev_waits
- num_regular_waits
- Average wait times (3 calculated)

**Utilization Metrics (per CS + general):**
- CS utilization rate
- Regular spot occupancy
- total_usage_time per CS

**Financial Metrics (8+):**
- total_revenue
- regular_revenue
- ev_revenue
- Revenue per hour
- Revenue per vehicle
- Revenue per CS
- Revenue contribution %

**Decision Metrics (8+):**
- EVs at CS count & %
- evs_chose_regular (3 reasons)
- regular_used_ev
- price_rejections per CS
- distance_rejections per CS

**TOTAL: 30+ metrics collected!** 📊

---

## 🎯 Most Important Metrics (Top 10)

1. **Average EV Wait Time** ⭐⭐⭐
2. **% EVs Using CS** ⭐⭐⭐
3. **Total Revenue** ⭐⭐⭐
4. **CS Utilization Rate** ⭐⭐
5. **Price Rejections** ⭐⭐
6. **Distance Rejections** ⭐⭐
7. **Revenue per Hour** ⭐⭐
8. **Service Rate** ⭐
9. **Regular vs EV Wait Time** ⭐
10. **CS Revenue Contribution** ⭐

---

## 📝 How to Access Metrics

### In Code

```python
from simulator import run_simulation

# Run simulation
parking_lot = run_simulation(verbose=False)

# Access metrics
print(f"Total EVs: {parking_lot.total_evs}")
print(f"EVs served: {parking_lot.evs_served}")
print(f"Total revenue: ${parking_lot.total_revenue:.2f}")

# Per CS metrics
for cs in parking_lot.charging_stations:
    print(f"{cs.name}: {cs.vehicles_served} vehicles")
    print(f"  Revenue: ${cs.total_revenue:.2f}")
    print(f"  Distance rejections: {cs.distance_rejections}")
    print(f"  Price rejections: {cs.price_rejections}")
```

### In Comparator

```python
# Run comparison
python3 comparator.py

# Output shows:
# - Metrics for each scheme
# - Metrics for each pricing strategy
# - TOP 10 combinations with key metrics
```

---

## 🏆 Conclusion

The project implements a **comprehensive metrics system** with:

- ✅ **30+ individual metrics**
- ✅ **5 major categories**
- ✅ **10 key KPIs**
- ✅ **Automatic collection**
- ✅ **Clear reporting**
- ✅ **Comparative analysis**

These metrics enable **complete analysis** of:
- Allocation schemes
- CS locations
- Pricing strategies
- User behavior
- System optimization

---

**Document:** METRICS.md  
**Version:** 1.0  
**Date:** October 2025

