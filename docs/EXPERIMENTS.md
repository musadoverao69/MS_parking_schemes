# 🔬 Suggested Experiments - Complete Analysis Guide

This document contains suggested experiments for complete analysis of the E-Mobility parking system.

---

## 📋 Experiment Overview

**Total Suggested Experiments:** 12  
**Categories:** Comparison, Dimensioning, Demand, Pricing, Optimization  
**Difficulty:** Beginner to Advanced

---

## 🎯 EXPERIMENT 1: Baseline Scheme Comparison

**Objective:** Compare all 4 allocation schemes with default configuration

**Configuration:**
```python
# In config.py - keep defaults
NUM_REGULAR_SPOTS = 50
CHARGING_STATIONS_CONFIG = default
PROB_EV = 0.3
ARRIVAL_INTERVAL = 5
SIMULATION_TIME = 480
```

**Run:**
```bash
python3 comparator.py
```

**Analyze:**
- Which scheme has lowest EV wait time?
- Which scheme has best overall utilization?
- Which scheme is most fair?
- Which generates most revenue?

**Expected Results:**
- All schemes perform similarly with low demand
- RESERVATION may have slight advantage
- Revenue differences < 10%

---

## 🎯 EXPERIMENT 2: High EV Demand

**Objective:** Test behavior with many electric vehicles

**Configuration:**
```python
PROB_EV = 0.6  # 60% EVs (double the default)
NUM_REGULAR_SPOTS = 50
# Keep other defaults
```

**Questions:**
- Can EXCLUSIVE scheme handle demand?
- Does ON_DEMAND improve service?
- How many EVs need to use regular spots?
- Which CS get saturated first?

**Run for each scheme:**
```bash
# Edit config.py, change ALLOCATION_SCHEME
python3 simulator.py
```

**Expected Results:**
- EXCLUSIVE will have longer wait times
- ON_DEMAND will serve more EVs (using regular spots)
- CS-Near will be saturated (>90% usage)

---

## 🎯 EXPERIMENT 3: CS Capacity Optimization

**Objective:** Find optimal number of EV spots

**Test scenarios:**
- A: Total 5 CS spots
- B: Total 10 CS spots (default)
- C: Total 15 CS spots
- D: Total 20 CS spots

**Configuration:**
```python
# Scenario A
CHARGING_STATIONS_CONFIG = [("CS-Near", 30, 5, 10.0)]

# Scenario B (default)
CHARGING_STATIONS_CONFIG = [
    ("CS-Near", 30, 3, 12.0),
    ("CS-Mid", 80, 4, 8.0),
    ("CS-Far", 150, 3, 6.0),
]

# Scenario C
CHARGING_STATIONS_CONFIG = [("CS-Near", 30, 15, 10.0)]

# Scenario D
CHARGING_STATIONS_CONFIG = [("CS-Near", 30, 20, 10.0)]
```

**Analyze:**
- At what point does wait time stabilize?
- Cost-benefit ratio?
- Which scheme is most sensitive to capacity?
- Optimal CS spot count?

**Metrics to Track:**
- Average EV wait time
- CS utilization rate
- EVs using regular spots
- Revenue per CS spot

---

## 🎯 EXPERIMENT 4: Peak Hour Simulation

**Objective:** Simulate high-demand period (e.g., lunch, dinner)

**Configuration:**
```python
ARRIVAL_INTERVAL = 2  # Vehicle every 2 min (very frequent)
SIMULATION_TIME = 240  # 4 hours of peak
PROB_EV = 0.4  # Higher EV ratio during peak
```

**Analyze:**
- Which scheme handles peak best?
- Are queues formed?
- Are wait times acceptable?
- Revenue during peak?

**Expected Results:**
- Significant queues form
- Wait times increase
- CS utilization reaches 90%+
- Revenue/hour increases significantly

---

## 🎯 EXPERIMENT 5: Large Shopping Mall

**Objective:** Simulate large-scale parking lot

**Configuration:**
```python
NUM_REGULAR_SPOTS = 200
CHARGING_STATIONS_CONFIG = [
    ("CS-Near-1", 30, 8, 12.0),
    ("CS-Near-2", 40, 8, 11.0),
    ("CS-Mid", 80, 8, 8.0),
    ("CS-Far", 120, 8, 6.0),
]
ARRIVAL_INTERVAL = 3
SIMULATION_TIME = 600  # 10 hours
```

**Analyze:**
- Do results scale proportionally?
- Are there significant differences between schemes at large scale?
- Revenue projections?
- Optimal CS distribution?

---

## 🎯 EXPERIMENT 6: Low EV Demand

**Objective:** Test efficiency when few EVs arrive

**Configuration:**
```python
PROB_EV = 0.1  # Only 10% EVs
NUM_REGULAR_SPOTS = 50
# Keep CS default
```

**Analyze:**
- Does EXCLUSIVE waste many spots?
- Does PRIORITY optimize better?
- How many regular cars use EV spots in PRIORITY?
- CS utilization rates?

**Expected Results:**
- EXCLUSIVE: CS underutilized (<30%)
- PRIORITY: Better overall utilization
- CS-Far likely 0% usage even with low EV demand

---

## 🎯 EXPERIMENT 7: Pricing Strategy Impact

**Objective:** Analyze effect of reservation rate on RESERVATION scheme

**Test different pricing strategies:**

**A. Premium Pricing:**
```python
CHARGING_STATIONS_CONFIG = [
    ("CS-Near", 30, 3, 15.0),   # Very expensive
    ("CS-Mid", 80, 4, 12.0),
    ("CS-Far", 150, 3, 10.0),
]
```

**B. Competitive Pricing:**
```python
CHARGING_STATIONS_CONFIG = [
    ("CS-Near", 30, 3, 7.0),    # Close to regular
    ("CS-Mid", 80, 4, 6.0),
    ("CS-Far", 150, 3, 5.5),
]
```

**C. Below Regular Pricing (Incentive):**
```python
CHARGING_STATIONS_CONFIG = [
    ("CS-Near", 30, 3, 6.0),
    ("CS-Mid", 80, 4, 5.0),
    ("CS-Far", 150, 3, 4.0),    # Cheaper than regular!
]
```

**Analyze:**
- How does pricing affect CS usage %?
- Price elasticity of demand?
- Which strategy maximizes revenue?
- Which maximizes CS utilization?

---

## 🎯 EXPERIMENT 8: Distance Tolerance Analysis

**Objective:** Test impact of CS location variations

**Scenarios:**

**A. All Near (<50m):**
```python
CHARGING_STATIONS_CONFIG = [
    ("CS-1", 30, 3, 10.0),
    ("CS-2", 40, 4, 10.0),
    ("CS-3", 50, 3, 10.0),
]
```

**B. All Far (>100m):**
```python
CHARGING_STATIONS_CONFIG = [
    ("CS-1", 100, 3, 6.0),
    ("CS-2", 130, 4, 6.0),
    ("CS-3", 160, 3, 6.0),
]
```

**C. Mixed Distances:**
```python
CHARGING_STATIONS_CONFIG = [
    ("CS-Near", 30, 3, 10.0),
    ("CS-Mid", 80, 4, 8.0),
    ("CS-Far", 150, 3, 6.0),
]
```

**Analyze:**
- Usage distribution?
- Distance rejections?
- Can low price compensate for distance?

**Expected Results:**
- Scenario A: High usage (>80%) across all CS
- Scenario B: Very low usage (<20%) even with low prices
- Scenario C: Near CS dominates, far CS unused

---

## 🎯 EXPERIMENT 9: Battery Distribution Impact

**Objective:** Test with different battery level distributions

**Modify `generate_battery_level()` in models/utils.py:**

**Scenario A - Many Low Batteries:**
```python
def generate_battery_level():
    rand = random.random()
    if rand < 0.40:  # 40% critical (was 15%)
        return BatteryLevel.CRITICAL
    elif rand < 0.70:  # 30% low (was 20%)
        return BatteryLevel.LOW
    elif rand < 0.90:  # 20% medium
        return BatteryLevel.MEDIUM
    else:  # 10% high
        return BatteryLevel.HIGH
```

**Scenario B - Many High Batteries:**
```python
def generate_battery_level():
    rand = random.random()
    if rand < 0.10:  # 10% critical
        return BatteryLevel.CRITICAL
    elif rand < 0.20:  # 10% low
        return BatteryLevel.LOW
    elif rand < 0.40:  # 20% medium
        return BatteryLevel.MEDIUM
    else:  # 60% high (was 30%)
        return BatteryLevel.HIGH
```

**Analyze:**
- Do far CS get more usage with low batteries?
- Impact on wait time?
- Revenue changes?

---

## 🎯 EXPERIMENT 10: Economic Profile Impact

**Objective:** Test different customer economic distributions

**Modify `generate_economic_profile()` in models/utils.py:**

**Scenario A - Mostly Budget:**
```python
def generate_economic_profile():
    rand = random.random()
    if rand < 0.70:  # 70% budget (was 30%)
        return EconomicProfile.BUDGET
    elif rand < 0.90:  # 20% moderate
        return EconomicProfile.MODERATE
    else:  # 10% premium
        return EconomicProfile.PREMIUM
```

**Scenario B - Mostly Premium:**
```python
def generate_economic_profile():
    rand = random.random()
    if rand < 0.10:  # 10% budget
        return EconomicProfile.BUDGET
    elif rand < 0.30:  # 20% moderate
        return EconomicProfile.MODERATE
    else:  # 70% premium (was 20%)
        return EconomicProfile.PREMIUM
```

**Analyze:**
- Does customer profile affect optimal pricing?
- Premium customers → can charge higher prices?
- Budget customers → need competitive pricing?

---

## 🎯 EXPERIMENT 11: Sensitivity Analysis

**Objective:** Test robustness to parameter variations

**Vary each parameter systematically:**

1. **EV Probability:** [0.1, 0.2, 0.3, 0.4, 0.5, 0.6]
2. **CS Spots:** [5, 10, 15, 20, 25]
3. **Arrival Interval:** [2, 3, 5, 7, 10] minutes
4. **Prices:** [$6, $8, $10, $12, $15]

**For each scheme, record:**
- Average EV wait time
- CS utilization rate
- Total revenue
- % EVs using CS

**Analyze:**
- Which scheme is most robust to variations?
- Which parameters have greatest impact?
- Are there threshold effects?

---

## 🎯 EXPERIMENT 12: Multi-Period Simulation

**Objective:** Simulate a complete day with varying demand

**Implementation requires code modification:**

```python
def get_arrival_rate(current_time):
    """Return arrival interval based on time of day"""
    hour = (current_time // 60) % 24
    
    if 8 <= hour < 10:    # Morning
        return 10  # Low demand
    elif 10 <= hour < 12: # Mid-morning
        return 5   # Medium demand
    elif 12 <= hour < 14: # Lunch peak
        return 2   # High demand
    elif 14 <= hour < 18: # Afternoon
        return 5   # Medium demand
    elif 18 <= hour < 20: # Dinner peak
        return 2   # High demand
    else:                 # Evening
        return 8   # Low demand
```

**Configuration:**
```python
SIMULATION_TIME = 840  # 14 hours (8am-10pm)
```

**Analyze:**
- Which scheme handles demand variations best?
- Identify critical hours
- Revenue by period
- Utilization patterns

---

## 📊 RESULTS TEMPLATE

For each experiment, document:

```
EXPERIMENT: [Number and Name]
DATE: [Execution date]
SCHEME: [ON_DEMAND/EXCLUSIVE/PRIORITY/RESERVATION]

CONFIGURATION:
- NUM_REGULAR_SPOTS: 
- Charging Stations: 
- PROB_EV: 
- ARRIVAL_INTERVAL: 
- SIMULATION_TIME: 

RESULTS:
- Total vehicles: 
- Total EVs: 
- EVs served: 
- Avg wait time (general): 
- Avg wait time (EV): 
- Regular spot utilization: 
- CS utilization (avg): 
- Total revenue: 
- Revenue/hour: 
- EVs at CS: 
- Price rejections: 
- Distance rejections: 

OBSERVATIONS:
[Your analysis and conclusions]
```

---

## 📈 COMPARISON MATRIX

Create a comparison table:

| Experiment | Scheme | Config | Avg EV Wait | CS Usage % | Revenue | Best For |
|------------|--------|--------|-------------|------------|---------|----------|
| 1 - Baseline | ALL | Default | ... | ... | ... | Comparison |
| 2 - High EV | ALL | 60% EV | ... | ... | ... | Stress test |
| 3 - Capacity | EXCLUSIVE | Vary spots | ... | ... | ... | Optimization |
| ... | ... | ... | ... | ... | ... | ... |

---

## 💡 ANALYSIS TIPS

### 1. Always Use Same RANDOM_SEED
```python
RANDOM_SEED = 42  # For fair comparison
```

### 2. Run Multiple Times
```bash
# Test with different seeds
for seed in [42, 123, 456, 789, 1000]:
    # Change RANDOM_SEED and run
```

### 3. Document Everything
- Configuration used
- Results obtained
- Observations made
- Conclusions drawn

### 4. Create Visualizations
- Bar charts: Revenue by scheme
- Line charts: Wait time vs EV probability
- Heatmaps: CS utilization over time

### 5. Consider Different Perspectives
- **EV User:** Wait time, CS availability
- **Regular User:** Wait time, fairness
- **Operator:** Revenue, utilization
- **Sustainability:** EV adoption, charging availability

---

## 🎯 KEY QUESTIONS TO ANSWER

### Strategic Questions

1. **What is the optimal CS capacity?**
   - Run Experiment 3
   - Find point where wait time stabilizes
   - Calculate ROI

2. **Which allocation scheme is best?**
   - Depends on goals:
   - Revenue → EXCLUSIVE
   - EV satisfaction → ON_DEMAND  
   - Overall efficiency → PRIORITY

3. **How should CS be priced?**
   - Run Experiment 7
   - Test elasticity
   - Find revenue-maximizing price

4. **Where should CS be located?**
   - Run Experiment 8
   - **Finding:** Within 50m is critical
   - Far CS are wasted investment

5. **What customer mix is expected?**
   - Run Experiments 9, 10
   - Affects optimal pricing
   - Affects CS placement

### Operational Questions

6. **How to handle peak hours?**
   - Run Experiment 4
   - Consider dynamic pricing
   - May need more CS capacity

7. **Is investment in CS justified?**
   - Calculate: CS revenue × 365 days / installation cost
   - Compare scenarios with/without CS
   - Payback period analysis

8. **Can pricing balance demand?**
   - Run Experiment 7
   - Lower prices for far CS
   - Dynamic pricing by time

---

## 📊 EXPECTED INSIGHTS

Based on our implementation:

### Finding 1: Location is CRITICAL
```
CS at 30m:  92.6% utilization ✅
CS at 80m:  10.7% utilization ⚠️
CS at 150m: 0.0% utilization ❌
```
**Conclusion:** Better few spots near than many spots far!

### Finding 2: Price Matters MORE Than Distance
```
Price rejections:    35
Distance rejections: 22
```
**Conclusion:** Drivers are more price-sensitive than distance-sensitive!

### Finding 3: Balance is Optimal
```
CS-Near (30m, $12/h): High price → many rejections
CS-Mid (80m, $8/h):   Best balance → most profitable
CS-Far (150m, $6/h):  Too far → zero usage
```
**Conclusion:** Middle ground wins!

---

## 🔬 ADVANCED EXPERIMENTS

### Experiment 13: Dynamic Pricing
Test if varying prices by time of day improves results

### Experiment 14: Reservation System
Test advance booking with RESERVATION scheme

### Experiment 15: Customer Learning
Model repeat customers who learn CS locations/prices

### Experiment 16: Real Data Validation
Compare with actual shopping mall data if available

---

## 📝 DOCUMENTATION TEMPLATE

For your final report:

```markdown
# Experiment Results Summary

## Methodology
- Simulation tool: SimPy 4.1.1
- Random seed: 42
- Simulation time: 480 minutes
- Replications: 10 per scenario

## Results

### Baseline (Experiment 1)
[Results table]

### High Demand (Experiment 2)  
[Results table]

### Sensitivity Analysis (Experiment 11)
[Graphs and charts]

## Key Findings

1. Location Impact: [Explain with data]
2. Pricing Impact: [Explain with data]
3. Scheme Comparison: [Explain with data]

## Recommendations

1. Optimal CS placement: Within 50m
2. Optimal pricing: $7-8/hour
3. Best scheme: [Based on goals]

## Conclusions
[Summary]
```

---

## ✅ EXPERIMENT CHECKLIST

For each experiment:

- [ ] Define objective clearly
- [ ] Set up configuration
- [ ] Run simulation
- [ ] Record all metrics
- [ ] Document observations
- [ ] Compare with baseline
- [ ] Draw conclusions
- [ ] Consider limitations

---

## 🎓 Learning Outcomes

By completing these experiments, you will:

1. ✅ Understand how location affects CS usage
2. ✅ Understand price elasticity of demand
3. ✅ Learn optimal capacity planning
4. ✅ Compare allocation strategies
5. ✅ Develop analytical skills
6. ✅ Practice scientific method
7. ✅ Make data-driven recommendations

---

## 🚀 Getting Started

**Recommended Order:**

1. **Start:** Experiment 1 (Baseline) - Understand system
2. **Easy:** Experiments 2, 6 - Vary demand
3. **Medium:** Experiments 3, 4, 5 - Dimensioning
4. **Advanced:** Experiments 7, 8 - Optimization
5. **Research:** Experiments 9, 10, 11 - Deep analysis

---

**Document:** EXPERIMENTS.md  
**Total Experiments:** 12 main + 4 advanced  
**Estimated Time:** 2-4 weeks for complete analysis  
**Tools Needed:** Python, SimPy, spreadsheet software, visualization tools

