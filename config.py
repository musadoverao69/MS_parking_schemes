"""
Centralized Project Configuration

All simulation settings in one place.
Modify here to adjust simulation behavior.
"""
from models import AllocationScheme, BatteryLevel, EconomicProfile

# ============================================================================
# GENERAL SIMULATION SETTINGS
# ============================================================================

RANDOM_SEED = 42# Seed for reproducibility
NUM_REGULAR_SPOTS = 20# Number of regular parking spots
SIMULATION_TIME = 480# Time in minutes (480 = 8 hours)
ARRIVAL_INTERVAL = 10# Minutes between arrivals (average)
PROB_EV = 0.3# Probability of vehicle being EV (30%)
PARKING_TIME = (30, 120)           # Min and max parking duration (minutes)
PROB_RESERVATION = 0.4# Probability of EV having reservation (40%)

# ============================================================================
# ALLOCATION SCHEME
# ============================================================================

# Options: ON_DEMAND, RESERVATION
ALLOCATION_SCHEME = AllocationScheme.ON_DEMAND

# ============================================================================
# PRICES ($ per hour)
# ============================================================================

REGULAR_SPOT_PRICE = 5.0# Regular spot price

# ============================================================================
# CHARGING STATIONS
# ============================================================================

# Format: (name, distance_meters, num_spots, price_per_hour)
CHARGING_STATIONS_CONFIG = [
    ("CS-Near", 30, 3, 12.0),
    ("CS-Mid", 80, 4, 8.0),
    ("CS-Far", 150, 3, 6.0),
]

# ============================================================================
# DECISION TOLERANCES
# ============================================================================

# Maximum acceptable distance by battery level (meters)
DISTANCE_TOLERANCE_BY_BATTERY = {
    BatteryLevel.CRITICAL: 200,  # Accepts any distance
    BatteryLevel.LOW: 120,       # Accepts up to 120m
    BatteryLevel.MEDIUM: 80,     # Prefers up to 80m
    BatteryLevel.HIGH: 50,       # Only accepts very close
}

# Price tolerance by battery level (% over regular spot price)
PRICE_TOLERANCE_BY_BATTERY = {
    BatteryLevel.CRITICAL: 300,   # Accepts up to 3x the price
    BatteryLevel.LOW: 200,        # Accepts up to 2x
    BatteryLevel.MEDIUM: 150,     # Accepts up to 1.5x
    BatteryLevel.HIGH: 120,       # Accepts up to 1.2x
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

# Pricing strategies (function returns price based on distance)
PRICING_STRATEGIES = {
    "Premium": lambda dist: 12.0 if dist <= 50 else (8.0 if dist <= 100 else 6.0),
    "Competitive": lambda dist: 7.0 if dist <= 50 else (6.0 if dist <= 100 else 5.5),
    "Uniform": lambda dist: 8.0,  # Single price for all CS
}
