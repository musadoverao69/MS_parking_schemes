"""
Shared utility functions
"""
import random
from .enums import BatteryLevel, EconomicProfile


def generate_battery_level():
    """
    Generates a random battery level for an EV
    
    Distribution:
    - 15% CRITICAL (< 20%)
    - 20% LOW (20-40%)
    - 35% MEDIUM (40-70%)
    - 30% HIGH (> 70%)
    
    Returns:
        BatteryLevel: Generated battery level
    """
    rand = random.random()
    if rand < 0.15:
        return BatteryLevel.CRITICAL
    elif rand < 0.35:
        return BatteryLevel.LOW
    elif rand < 0.70:
        return BatteryLevel.MEDIUM
    else:
        return BatteryLevel.HIGH


def generate_economic_profile():
    """
    Generates a random economic profile
    
    Distribution:
    - 30% BUDGET (very price sensitive)
    - 50% MODERATE (average sensitivity)
    - 20% PREMIUM (low price sensitivity)
    
    Returns:
        EconomicProfile: Generated economic profile
    """
    rand = random.random()
    if rand < 0.30:
        return EconomicProfile.BUDGET
    elif rand < 0.80:
        return EconomicProfile.MODERATE
    else:
        return EconomicProfile.PREMIUM

