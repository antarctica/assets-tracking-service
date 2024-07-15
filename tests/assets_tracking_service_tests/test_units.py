from assets_tracking_service.units import UnitsConverter


class TestUnits:
    def test__km_h__to__m_s(self):
        """Converts from km/h to m/s."""
        converter = UnitsConverter()
        assert converter.kilometers_per_hour_to_meters_per_second(100) == 27.77777777777778

    def test__knots__to__m_s(self):
        """Converts from knots to m/s."""
        converter = UnitsConverter()
        assert converter.knots_to_meters_per_second(100) == 51.44444444444445

    def test__feet__to__meters(self):
        """Converts from feet to meters."""
        converter = UnitsConverter()
        assert converter.feet_to_meters(100) == 30.479999999999997

    def test__timestamp_milliseconds__to__timestamp(self):
        """Converts timestamp with milliseconds to timestamp without."""
        assert UnitsConverter.timestamp_milliseconds_to_timestamp(1635980000000) == 1635980000
