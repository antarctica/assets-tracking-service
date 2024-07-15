from pint import UnitRegistry


class UnitsConverter:
    """Convert between different units (e.g. speed)."""

    def __init__(self):
        self._units = UnitRegistry()

    def kilometers_per_hour_to_meters_per_second(self, speed: float) -> float:
        """Convert velocity from km/h to m/s."""
        km_h = speed * self._units.parse_units("kilometer/hour")
        return km_h.to(self._units.meter / self._units.second).magnitude

    def knots_to_meters_per_second(self, speed: float) -> float:
        """Convert velocity from knots to m/s."""
        knots = speed * self._units.parse_units("knot")
        return knots.to(self._units.meter / self._units.second).magnitude

    def feet_to_meters(self, distance: float) -> float:
        """Convert distance from feet to meters."""
        feet = distance * self._units.parse_units("foot")
        return feet.to(self._units.meter).magnitude

    @staticmethod
    def timestamp_milliseconds_to_timestamp(time: int) -> int:
        """Convert timestamp with milliseconds to timestamp without."""
        return int(time / 1000)
