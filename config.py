"""
Centralized Project Configuration

All simulation settings in one place.
Modify here to adjust simulation behavior.
"""
from models import AllocationScheme, BatteryLevel, EconomicProfile

# ============================================================================
# GENERAL SIMULATION SETTINGS
# ============================================================================

RANDOM_SEED = 72# Seed for reproducibility
NUM_REGULAR_SPOTS = 50# Number of regular parking spots
SIMULATION_TIME = 480# Time in minutes (480 = 8 hours)
ARRIVAL_INTERVAL = 2# Minutes between arrivals (average)
PROB_EV = 0.3# Probability of vehicle being EV (30%)
PARKING_TIME = (30, 120)# Min and max parking duration (minutes)
PROB_RESERVATION = 0.4# Probability of EV having reservation (40%)

# ============================================================================
# ALLOCATION SCHEME
# ============================================================================

# Options: ON_DEMAND, RESERVATION
ALLOCATION_SCHEME = AllocationScheme.ON_DEMAND

# ============================================================================
# PRICES ($ per hour)
# ============================================================================

REGULAR_SPOT_PRICE = 2.6# Regular spot price (base parking price)

# Base parking price for charging stations (same as regular or can be different)
CHARGING_STATION_PARKING_PRICE = 2.6# Base parking price per hour for CS spots

# ============================================================================
# CHARGING STATIONS
# ============================================================================

# Charging options available (speed_kw, price_per_kwh, name)
# Based on Portugal pricing: Normal charging up to €0.43/kWh, Fast charging up to €0.79/kWh
# Note: Price is ONLY for charging, NO parking fee included
CHARGING_OPTIONS = {
    "Normal": (7.0, 0.43, "Normal"),      # 7kW × €0.43/kWh = €3.01/h (charging only)
    "Fast": (22.0, 0.43, "Fast"),         # 22kW × €0.43/kWh = €9.46/h (charging only)
    "Ultra-fast": (50.0, 0.79, "Ultra-fast"),  # 50kW × €0.79/kWh = €39.50/h (charging only)
}

# Format: (name, distance_meters, num_spots, [list of available charging option names])
# Each station can offer multiple charging speeds - vehicles choose based on their economic profile
CHARGING_STATIONS_CONFIG = [
    ("CS-Near", 30, 3, ["Normal", "Fast", "Ultra-fast"]),   # All options available
    ("CS-Mid", 80, 4, ["Normal", "Fast", "Ultra-fast"]),    # All options available
    ("CS-Far", 150, 3, ["Normal", "Fast", "Ultra-fast"]),   # All options available
]

# ============================================================================
# DECISION TOLERANCES
# ============================================================================

# Maximum acceptable distance by battery level (meters)
DISTANCE_TOLERANCE_BY_BATTERY = {
    BatteryLevel.CRITICAL: 200,  # Accepts any distance
    BatteryLevel.LOW: 150,       # Accepts up to 150m
    BatteryLevel.MEDIUM: 100,     # Prefers up to 100m
    BatteryLevel.HIGH: 50,       # Only accepts very close
}

# Price tolerance by battery level (% over regular spot price)
# Note: Since charging is an additional service (not parking fee), these tolerances
# apply to the charging price itself. Higher battery = less willing to pay for charging.
PRICE_TOLERANCE_BY_BATTERY = {
    BatteryLevel.CRITICAL: 300,   # Accepts up to 3x the regular spot price for charging
    BatteryLevel.LOW: 200,        # Accepts up to 2x
    BatteryLevel.MEDIUM: 120,     # Accepts up to 1.2x
    BatteryLevel.HIGH: 180,      # Accepts up to 1.8x (increased from 120% to allow Normal charging at €3.01)
}

# Tolerance multiplier by economic profile
PRICE_TOLERANCE_BY_PROFILE = {
    EconomicProfile.BUDGET: 0.8,      # Reduces 20%
    EconomicProfile.MODERATE: 1.0,    # Maintains
    EconomicProfile.PREMIUM: 1.5,     # Increases 50%
}

# ============================================================================
# COMPARISON CONFIGURATIONS
# ============================================================================

# CS configurations for comparison (without prices - applied by strategy)
CS_CONFIGS_COMPARISON = {
    "Near": [
        ("CS-1", 30, 3),
        ("CS-2", 40, 4),
        ("CS-3", 50, 3),
    ],
    "Mixed": [
        ("CS-Near", 30, 3),
        ("CS-Mid", 80, 4),
        ("CS-Far", 150, 3),
    ],
    "Concentrated": [
        ("CS-Main", 30, 10),
    ],
}

# Pricing strategies (function returns tuple: (charging_speed_kw, price_per_kwh))
# Note: Distance no longer affects price, only customer tolerance
PRICING_STRATEGIES = {
    "Premium": lambda dist: (50.0, 0.79),      # Ultra-fast: 50kW × €0.79/kWh
    "Competitive": lambda dist: (22.0, 0.43),  # Fast: 22kW × €0.43/kWh
    "Normal": lambda dist: (7.0, 0.43),        # Normal: 7kW × €0.43/kWh
    "Uniform": lambda dist: (22.0, 0.43),      # Uniform fast charging for all
}
