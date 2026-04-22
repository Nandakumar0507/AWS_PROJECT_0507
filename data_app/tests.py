from django.test import TestCase

from analytics_app.services import contact_area_pct, peak_pressure_index


class AnalyticsServiceTests(TestCase):
    def test_peak_pressure_index_noise_filter(self):
        matrix = [[0 for _ in range(32)] for _ in range(32)]
        matrix[0][0] = 4000
        self.assertEqual(peak_pressure_index(matrix), 0.0)

    def test_contact_area_pct(self):
        matrix = [[0 for _ in range(32)] for _ in range(32)]
        for i in range(16):
            matrix[0][i] = 200
        self.assertGreater(contact_area_pct(matrix), 0)
