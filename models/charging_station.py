"""
ChargingStation class - Represents a charging station with multiple charging options
"""
from dataclasses import dataclass
from typing import List, Optional
import simpy


@dataclass
class ChargingOption:
    """
    Represents a charging option (speed and price) available at a station
    
    Attributes:
        speed_kw: Charging speed in kilowatts (kW)
        price_per_kwh: Price per kilowatt-hour (€/kWh)
        name: Name of the option (e.g., "Normal", "Fast", "Ultra-fast")
    """
    speed_kw: float
    price_per_kwh: float
    name: str = ""
    
    def calculate_price_per_hour(self) -> float:
        """Calculate charging price per hour: speed_kw × price_per_kwh (no parking fee)"""
        return self.speed_kw * self.price_per_kwh


@dataclass
class ChargingStation:
    """
    Represents a charging station in the parking lot with multiple charging options
    
    Attributes:
        id: Unique identifier
        name: Station name
        distance_from_entrance: Distance in meters from mall entrance
        num_spots: Number of available spots at this station
        charging_options: List of available charging options (Normal, Fast, Ultra-fast)
        parking_price_per_hour: Base parking price per hour (€/h)
        resource: SimPy resource for queue management
        resource_priority: SimPy priority resource (for RESERVATION scheme)
        
    Statistics:
        vehicles_served: Total vehicles served
        total_usage_time: Total usage time in minutes
        total_revenue: Total revenue generated
        distance_rejections: Rejections due to distance
        price_rejections: Rejections due to price
    """
    id: int
    name: str
    distance_from_entrance: float
    num_spots: int
    charging_options: List[ChargingOption]
    parking_price_per_hour: float = 0.0
    resource: simpy.Resource = None
    resource_priority: simpy.PriorityResource = None
    
    # Statistics
    vehicles_served: int = 0
    total_usage_time: float = 0.0
    total_revenue: float = 0.0
    distance_rejections: int = 0
    price_rejections: int = 0
    
    def get_best_option(self, max_price: float) -> Optional[ChargingOption]:
        """
        Get the best charging option that fits within max_price
        Returns the fastest option that is affordable, or None if none fit
        """
        affordable_options = [
            opt for opt in self.charging_options
            if opt.calculate_price_per_hour() <= max_price
        ]
        if not affordable_options:
            return None
        # Return the fastest affordable option
        return max(affordable_options, key=lambda opt: opt.speed_kw)
    
    def get_cheapest_option(self) -> ChargingOption:
        """Get the cheapest charging option"""
        return min(self.charging_options, key=lambda opt: opt.calculate_price_per_hour())
    
    def get_fastest_option(self) -> ChargingOption:
        """Get the fastest charging option"""
        return max(self.charging_options, key=lambda opt: opt.speed_kw)

