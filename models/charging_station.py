"""
ChargingStation class - Represents a charging station
"""
from dataclasses import dataclass
import simpy


@dataclass
class ChargingStation:
    """
    Represents a charging station in the parking lot
    
    Attributes:
        id: Unique identifier
        name: Station name
        distance_from_entrance: Distance in meters from mall entrance
        num_spots: Number of available spots at this station
        price_per_hour: Price per hour ($)
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
    price_per_hour: float = 0.0
    resource: simpy.Resource = None
    resource_priority: simpy.PriorityResource = None
    
    # Statistics
    vehicles_served: int = 0
    total_usage_time: float = 0.0
    total_revenue: float = 0.0
    distance_rejections: int = 0
    price_rejections: int = 0

