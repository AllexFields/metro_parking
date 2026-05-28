"""
core/models.py
Vehicle, ParkingSlot, and ParkingLot classes.
Pure Python — no Streamlit dependency here.
"""

import re
import math
from datetime import datetime

RATE_TWO_WHEELER  = 10   # ₹ per hour
RATE_FOUR_WHEELER = 20   # ₹ per hour
OVERSTAY_HOURS    = 12

VEHICLE_PATTERN = re.compile(r'^[A-Z]{2}\d{2}[A-Z]{1,2}\d{4}$')


class Vehicle:
    TYPES = {"2W": "Two-Wheeler", "4W": "Four-Wheeler"}

    def __init__(self, number: str, vehicle_type: str, entry_time: datetime = None):
        number = number.strip().upper()
        if not VEHICLE_PATTERN.match(number):
            raise ValueError(f"Invalid number plate '{number}'. Expected format: GJ01AB1234")
        if vehicle_type not in self.TYPES:
            raise ValueError(f"Vehicle type must be '2W' or '4W'")
        self.number       = number
        self.vehicle_type = vehicle_type
        self.entry_time   = entry_time or datetime.now()

    def hourly_rate(self):
        return RATE_TWO_WHEELER if self.vehicle_type == "2W" else RATE_FOUR_WHEELER

    def duration_hours(self):
        return (datetime.now() - self.entry_time).total_seconds() / 3600

    def compute_fee(self):
        hours = max(1, math.ceil(self.duration_hours()))
        return hours * self.hourly_rate()

    def is_overstay(self):
        return self.duration_hours() > OVERSTAY_HOURS

    def to_dict(self):
        return {
            "number"      : self.number,
            "vehicle_type": self.vehicle_type,
            "entry_time"  : self.entry_time.strftime("%Y-%m-%d %H:%M:%S"),
        }


class ParkingSlot:
    def __init__(self, slot_id: str, slot_type: str):
        self.slot_id   = slot_id
        self.slot_type = slot_type
        self.vehicle   = None

    @property
    def is_empty(self):
        return self.vehicle is None

    def park(self, vehicle: Vehicle):
        if not self.is_empty:
            raise RuntimeError(f"Slot {self.slot_id} is already occupied.")
        self.vehicle = vehicle

    def vacate(self):
        if self.is_empty:
            raise RuntimeError(f"Slot {self.slot_id} is already empty.")
        v = self.vehicle
        self.vehicle = None
        return v


class ParkingLot:
    def __init__(self, station_name: str, two_wheeler_count: int, four_wheeler_count: int):
        self.station_name = station_name
        self.slots: dict[str, ParkingSlot] = {}
        for i in range(1, two_wheeler_count + 1):
            sid = f"2W-{i:02d}"
            self.slots[sid] = ParkingSlot(sid, "2W")
        for i in range(1, four_wheeler_count + 1):
            sid = f"4W-{i:02d}"
            self.slots[sid] = ParkingSlot(sid, "4W")

    def available_slots(self, vtype):
        return [s for s in self.slots.values() if s.slot_type == vtype and s.is_empty]

    def occupied_slots(self, vtype=None):
        if vtype:
            return [s for s in self.slots.values() if s.slot_type == vtype and not s.is_empty]
        return [s for s in self.slots.values() if not s.is_empty]

    def find_vehicle(self, number: str):
        number = number.strip().upper()
        for slot in self.slots.values():
            if not slot.is_empty and slot.vehicle.number == number:
                return slot
        return None

    def is_full(self, vtype):
        return len(self.available_slots(vtype)) == 0

    def park_vehicle(self, vehicle: Vehicle) -> ParkingSlot:
        available = self.available_slots(vehicle.vehicle_type)
        if not available:
            raise RuntimeError(f"No {vehicle.TYPES[vehicle.vehicle_type]} slots available!")
        slot = available[0]
        slot.park(vehicle)
        return slot

    def exit_vehicle(self, number: str):
        slot = self.find_vehicle(number)
        if slot is None:
            raise RuntimeError(f"Vehicle {number} not found.")
        vehicle = slot.vacate()
        fee = vehicle.compute_fee()
        return vehicle, slot, fee

    def overstay_alerts(self):
        for slot in self.slots.values():
            if not slot.is_empty and slot.vehicle.is_overstay():
                yield slot.vehicle, slot.slot_id, round(slot.vehicle.duration_hours(), 1)

    def capacity_summary(self):
        summary = {}
        for vtype in ("2W", "4W"):
            total    = sum(1 for s in self.slots.values() if s.slot_type == vtype)
            occupied = sum(1 for s in self.slots.values() if s.slot_type == vtype and not s.is_empty)
            summary[vtype] = {"total": total, "occupied": occupied, "free": total - occupied}
        return summary

    def all_slots_as_list(self):
        """Return slot data as list of dicts — for DataFrame rendering."""
        rows = []
        for slot in self.slots.values():
            rows.append({
                "Slot ID"     : slot.slot_id,
                "Type"        : "Two-Wheeler" if slot.slot_type == "2W" else "Four-Wheeler",
                "Status"      : "🔴 Occupied" if not slot.is_empty else "🟢 Free",
                "Vehicle"     : slot.vehicle.number if not slot.is_empty else "—",
                "Entry Time"  : slot.vehicle.entry_time.strftime("%H:%M  %d %b") if not slot.is_empty else "—",
                "Duration(h)" : round(slot.vehicle.duration_hours(), 2) if not slot.is_empty else 0,
                "Est. Fee (₹)": slot.vehicle.compute_fee() if not slot.is_empty else 0,
            })
        return rows
