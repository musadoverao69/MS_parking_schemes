"""
Enumerations used in the project
"""
from enum import Enum


class AllocationScheme(Enum):
    """Parking allocation schemes"""
    ON_DEMAND = "on_demand"      # EVs try EV spots first, can use regular if needed
    RESERVATION = "reservation"  # System with advance reservations


class BatteryLevel(Enum):
    """EV battery level"""
    CRITICAL = "critical"  # < 20% - MUST recharge
    LOW = "low"           # 20-40% - Prefers to recharge
    MEDIUM = "medium"     # 40-70% - May or may not recharge
    HIGH = "high"         # > 70% - Doesn't need to recharge


class EconomicProfile(Enum):
    """Price sensitivity profile"""
    BUDGET = "budget"        # Very price sensitive
    MODERATE = "moderate"    # Average sensitivity
    PREMIUM = "premium"      # Low price sensitivity

