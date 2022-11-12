#    Copyright (c) 2020 John A Kline <john@johnkline.com>
#
#    See the file LICENSE.txt for your full rights.
#
"""Test computing rainrates."""

import logging
import unittest

import weeutil.logger

import user.rainrate

log = logging.getLogger(__name__)

# Set up logging using the defaults.
weeutil.logger.setup('test_config', {})

class RainRateTests(unittest.TestCase):
    def test_add_packet(self):
        rain_entries = []
        ts = 1668104200

        # Add 100 pkts of zero rain.  Expect no entries.
        for i in range(100):
            pkt = { 'dateTime': ts, 'rain': 0.00, 'rainRate': 0.0 }
            user.rainrate.RainRate.add_packet(pkt, rain_entries)
            ts += 2
        self.assertEqual(len(rain_entries), 0)

        # Add a pkt of 0.01 rain.
        pkt = { 'dateTime': ts, 'rain': 0.01, 'rainRate': 0.0 }
        user.rainrate.RainRate.add_packet(pkt, rain_entries)
        self.assertEqual(len(rain_entries), 1)
        self.assertEqual(rain_entries[0], user.rainrate.RainEntry(expiration = ts + 900, timestamp = ts, amount = 0.01))
        ts += 2

        # Add 448 pkts of zero rain.  Entry above should still be present.
        for i in range(448):
            pkt = { 'dateTime': ts, 'rain': 0.00, 'rainRate': 0.0 }
            user.rainrate.RainRate.add_packet(pkt, rain_entries)
            ts += 2
        self.assertEqual(len(rain_entries), 1)
        self.assertEqual(rain_entries[0], user.rainrate.RainEntry(expiration = 1668104400 + 900, timestamp = 1668104400, amount = 0.01))

        # Add a pkt of 0.01 rain.  Should now have two entries.
        pkt = { 'dateTime': ts, 'rain': 0.01, 'rainRate': 0.0 }
        user.rainrate.RainRate.add_packet(pkt, rain_entries)
        self.assertEqual(len(rain_entries), 2)
        self.assertEqual(rain_entries[0], user.rainrate.RainEntry(expiration = ts + 900, timestamp = ts, amount = 0.01))
        self.assertEqual(rain_entries[1], user.rainrate.RainEntry(expiration = 1668104400 + 900, timestamp = 1668104400, amount = 0.01))
        ts += 2

        # Add a pkt of 0.00 rain. Expect first entry to top off.
        pkt = { 'dateTime': ts, 'rain': 0.00, 'rainRate': 0.0 }
        user.rainrate.RainRate.add_packet(pkt, rain_entries)
        self.assertEqual(len(rain_entries), 1)
        self.assertEqual(rain_entries[0], user.rainrate.RainEntry(expiration = 1668106198, timestamp = 1668105298, amount = 0.01))
        ts += 2

    def test_compute_rain_buckets(self):
        rain_entries = []
        ts = 1668104200

        # Add 100 pkts of zero rain.
        for i in range(100):
            pkt = { 'dateTime': ts, 'rain': 0.00, 'rainRate': 0.0 }
            user.rainrate.RainRate.add_packet(pkt, rain_entries)
            ts += 2
        rain_buckets = user.rainrate.RainRate.compute_rain_buckets(pkt, rain_entries)
        self.assertEqual(rain_buckets, [ 0.0 ] * 31)

        # Add 1000 pkts of 0.01 rain.
        for i in range(1000):
            pkt = { 'dateTime': ts, 'rain': 0.01, 'rainRate': 0.0 }
            user.rainrate.RainRate.add_packet(pkt, rain_entries)
            ts += 2

        rain_buckets = user.rainrate.RainRate.compute_rain_buckets(pkt, rain_entries)
        correct_buckets = [ 0.0, 0.15, 0.3, 0.45, 0.6, 0.75, 0.9, 1.05, 1.2, 1.35, 1.5, 1.65, 1.8, 1.95,
            2.1, 2.25, 2.4, 2.55, 2.7, 2.85, 3.0, 3.15, 3.3, 3.45, 3.6, 3.75, 3.9, 4.05, 4.2, 4.35, 4.5 ]
        self.assertEqual(len(rain_buckets), len(correct_buckets))
        for i in range(len(rain_buckets)):
            self.assertAlmostEqual(rain_buckets[i], correct_buckets[i], 7, 'index: %d' % i)

    def test_eliminate_buckets(self):

        # Add 100 pkts of 0.01 rain.
        rain_entries = []
        ts = 1668104200
        for i in range(100):
            pkt = { 'dateTime': ts, 'rain': 0.01, 'rainRate': 0.0 }
            user.rainrate.RainRate.add_packet(pkt, rain_entries)
            ts += 2
        rain_buckets = user.rainrate.RainRate.compute_rain_buckets(pkt, rain_entries)
        user.rainrate.RainRate.eliminate_buckets(rain_buckets)
        self.assertEqual(rain_buckets[1], 0.0)
        self.assertEqual(rain_buckets[2], 0.0)

        # Advance ts to clear out entries
        ts += 900

        # Add a single 0.01 pkt.  All buckets, except 30, should be zeroed.
        pkt = { 'dateTime': ts, 'rain': 0.01, 'rainRate': 0.0 }
        user.rainrate.RainRate.add_packet(pkt, rain_entries)
        ts += 2
        rain_buckets = user.rainrate.RainRate.compute_rain_buckets(pkt, rain_entries)
        user.rainrate.RainRate.eliminate_buckets(rain_buckets)
        correct_buckets = [ 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.00,
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.01 ]
        self.assertEqual(len(rain_buckets), len(correct_buckets))
        for i in range(len(rain_buckets)):
            self.assertAlmostEqual(rain_buckets[i], correct_buckets[i], 7, 'index: %d' % i)

        # Add another 0.01 pkt.  Buckets 1-19 should be zero.
        pkt = { 'dateTime': ts, 'rain': 0.01, 'rainRate': 0.0 }
        user.rainrate.RainRate.add_packet(pkt, rain_entries)
        ts += 2
        rain_buckets = user.rainrate.RainRate.compute_rain_buckets(pkt, rain_entries)
        user.rainrate.RainRate.eliminate_buckets(rain_buckets)
        correct_buckets = [ 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
            0.0, 0.0, 0.0, 0.0, 0.02, 0.02, 0.02, 0.02, 0.02, 0.02, 0.02, 0.02, 0.02, 0.02, 0.02 ]
        self.assertEqual(len(rain_buckets), len(correct_buckets))
        for i in range(len(rain_buckets)):
            self.assertAlmostEqual(rain_buckets[i], correct_buckets[i], 7, 'index: %d' % i)

        # Add another 0.01 pkt.  Buckets 1-9 should be zero.
        pkt = { 'dateTime': ts, 'rain': 0.01, 'rainRate': 0.0 }
        user.rainrate.RainRate.add_packet(pkt, rain_entries)
        ts += 2
        rain_buckets = user.rainrate.RainRate.compute_rain_buckets(pkt, rain_entries)
        user.rainrate.RainRate.eliminate_buckets(rain_buckets)
        correct_buckets = [ 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.03, 0.03, 0.03, 0.03, 0.03, 0.03,
            0.03, 0.03, 0.03, 0.03, 0.03, 0.03, 0.03, 0.03, 0.03, 0.03, 0.03, 0.03, 0.03, 0.03, 0.03 ]
        self.assertEqual(len(rain_buckets), len(correct_buckets))
        for i in range(len(rain_buckets)):
            self.assertAlmostEqual(rain_buckets[i], correct_buckets[i], 7, 'index: %d' % i)

        # Add another 0.01 pkt.  Buckets 1-2 should be zero.
        pkt = { 'dateTime': ts, 'rain': 0.01, 'rainRate': 0.0 }
        user.rainrate.RainRate.add_packet(pkt, rain_entries)
        ts += 2
        rain_buckets = user.rainrate.RainRate.compute_rain_buckets(pkt, rain_entries)
        user.rainrate.RainRate.eliminate_buckets(rain_buckets)
        correct_buckets = [ 0.0, 0.0, 0.0, 0.00, 0.04, 0.04, 0.04, 0.04, 0.04, 0.04, 0.04, 0.04, 0.04, 0.04, 0.04, 0.04,
            0.04, 0.04, 0.04, 0.04, 0.04, 0.04, 0.04, 0.04, 0.04, 0.04, 0.04, 0.04, 0.04, 0.04, 0.04 ]
        self.assertEqual(len(rain_buckets), len(correct_buckets))
        for i in range(len(rain_buckets)):
            self.assertAlmostEqual(rain_buckets[i], correct_buckets[i], 7, 'index: %d' % i)

    def test_compute_rain_rates(self):
        rain_entries = []
        ts = 1668104200

        # Add one pkt of 0.01 rain.
        pkt = { 'dateTime': ts, 'rain': 0.01, 'rainRate': 0.0 }
        user.rainrate.RainRate.add_packet(pkt, rain_entries)
        ts += 2
        rain_buckets = user.rainrate.RainRate.compute_rain_buckets(pkt, rain_entries)
        user.rainrate.RainRate.eliminate_buckets(rain_buckets)
        rain_rates = user.rainrate.RainRate.compute_rain_rates(rain_buckets)
        self.assertEqual(rain_rates, [ 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.04])

        # Add one pkt of 0.01 rain.
        pkt = { 'dateTime': ts, 'rain': 0.01, 'rainRate': 0.0 }
        user.rainrate.RainRate.add_packet(pkt, rain_entries)
        ts += 2
        rain_buckets = user.rainrate.RainRate.compute_rain_buckets(pkt, rain_entries)
        user.rainrate.RainRate.eliminate_buckets(rain_buckets)
        rain_rates = user.rainrate.RainRate.compute_rain_rates(rain_buckets)
        self.assertEqual(rain_rates, [ 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
            0.0, 0.0, 0.0, 0.0, 0.12, 0.114, 0.109, 0.104, 0.1, 0.096, 0.092, 0.089, 0.086, 0.083, 0.08])

        # Add 360 pkts of no rain.  The two rain pkts should now be sitting in the 7-1/2 minute.
        for _ in range(400):
            pkt = { 'dateTime': ts, 'rain': 0.00, 'rainRate': 0.0 }
            user.rainrate.RainRate.add_packet(pkt, rain_entries)
            ts += 2
        rain_buckets = user.rainrate.RainRate.compute_rain_buckets(pkt, rain_entries)
        user.rainrate.RainRate.eliminate_buckets(rain_buckets)
        rain_rates = user.rainrate.RainRate.compute_rain_rates(rain_buckets)
        self.assertEqual(rain_rates, [ 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.089, 0.086, 0.083, 0.08])

    def test_compute_rain_rate(self):
        rain_entries = []
        ts = 1668104200

        # A single tip. 0.01 over 15m
        pkt = { 'dateTime': ts, 'rain': 0.01, 'rainRate': 0.0 }
        user.rainrate.RainRate.add_packet(pkt, rain_entries)
        user.rainrate.RainRate.compute_rain_rate(pkt, rain_entries)
        self.assertEqual(pkt['rainRate'], 0.04)

        # Another tip 2s later.  0.02 over 10m
        ts += 2
        pkt = { 'dateTime': ts, 'rain': 0.01, 'rainRate': 18.0 }
        user.rainrate.RainRate.add_packet(pkt, rain_entries)
        user.rainrate.RainRate.compute_rain_rate(pkt, rain_entries)
        self.assertEqual(pkt['rainRate'], 0.12)

        # Another tip 2s later.  0.03 over 5m
        ts += 2
        pkt = { 'dateTime': 1668104204, 'rain': 0.01, 'rainRate': 18.0 }
        user.rainrate.RainRate.add_packet(pkt, rain_entries)
        user.rainrate.RainRate.compute_rain_rate(pkt, rain_entries)
        self.assertEqual(pkt['rainRate'], 0.36)

        # Another tip 2s later.  0.04 over 2m
        ts += 2
        pkt = { 'dateTime': ts, 'rain': 0.01, 'rainRate': 18.0 }
        user.rainrate.RainRate.add_packet(pkt, rain_entries)
        user.rainrate.RainRate.compute_rain_rate(pkt, rain_entries)
        self.assertEqual(pkt['rainRate'], 1.2)

        # No tip for 112s, still in 2m band, no change in rainRate.
        for i in range(0, 112, 2):
            ts += 2
            pkt = { 'dateTime': ts, 'rain': 0.00, 'rainRate': 99.9 }
            user.rainrate.RainRate.add_packet(pkt, rain_entries)
            user.rainrate.RainRate.compute_rain_rate(pkt, rain_entries)
            self.assertEqual(pkt['rainRate'], 1.2)

        # Another tip 2s later. 0.03 over 2m = 0.9, 0.04 over 2.5m = 0.96, 0.04 over 3m = 0.8
        ts += 2
        pkt = { 'dateTime': ts, 'rain': 0.00, 'rainRate': 99.9 }
        user.rainrate.RainRate.add_packet(pkt, rain_entries)
        user.rainrate.RainRate.compute_rain_rate(pkt, rain_entries)
        self.assertEqual(pkt['rainRate'], 0.96)

    def test_compute_rain_rate2(self):
        rain_entries = []
        ts = 1668104200

        # A 0.02 in one pkt.
        pkt = { 'dateTime': ts, 'rain': 0.02, 'rainRate': 0.0 }
        user.rainrate.RainRate.add_packet(pkt, rain_entries)
        user.rainrate.RainRate.compute_rain_rate(pkt, rain_entries)
        self.assertEqual(pkt['rainRate'], 0.12)

        # Another tip 0.02 2s later.
        ts += 2
        pkt = { 'dateTime': ts, 'rain': 0.02, 'rainRate': 18.0 }
        user.rainrate.RainRate.add_packet(pkt, rain_entries)
        user.rainrate.RainRate.compute_rain_rate(pkt, rain_entries)
        self.assertEqual(pkt['rainRate'], 1.2)

        # No rain for 4:56
        for _ in range(148):
            ts += 2
            pkt = { 'dateTime': ts, 'rain': 0.0, 'rainRate': 18.0 }
            user.rainrate.RainRate.add_packet(pkt, rain_entries)
        # 0.04 over 5m
        user.rainrate.RainRate.compute_rain_rate(pkt, rain_entries)
        self.assertEqual(pkt['rainRate'], 0.48)

        # No rain for 5:00
        for _ in range(150):
            ts += 2
            pkt = { 'dateTime': ts, 'rain': 0.0, 'rainRate': 18.0 }
            user.rainrate.RainRate.add_packet(pkt, rain_entries)
        # 0.04 over 10m
        user.rainrate.RainRate.compute_rain_rate(pkt, rain_entries)
        self.assertEqual(pkt['rainRate'], 0.24)

        # No rain for 5:00
        for _ in range(150):
            ts += 2
            pkt = { 'dateTime': ts, 'rain': 0.0, 'rainRate': 18.0 }
            user.rainrate.RainRate.add_packet(pkt, rain_entries)
        # 0.04 over 15m
        user.rainrate.RainRate.compute_rain_rate(pkt, rain_entries)
        self.assertEqual(pkt['rainRate'], 0.16)

    def test_compute_rain_rate_50_percent(self):
        rain_entries = []
        ts = 1668104200

        # Every other pkt has rain.  That's 1800 pkts per hour with 900 having .01 rain.
        # Expect 900 * 0.01 = 9 inches per hour
        ctr = 0
        for _ in range(1000):
            pkt = { 'dateTime': ts, 'rain': 0.0, 'rainRate': 0.0 }
            if ctr % 2 == 0:
                pkt['rain'] = 0.01
            ctr += 1
            user.rainrate.RainRate.add_packet(pkt, rain_entries)
            ts += 2

        self.assertEqual(len(rain_entries), 225)
        user.rainrate.RainRate.compute_rain_rate(pkt, rain_entries)
        self.assertEqual(pkt['rainRate'], 9.0)

    def test_compute_rain_rate_one_in_15(self):
        rain_entries = []
        ts = 1668104200

        ctr = 0
        for _ in range(1000):
            pkt = { 'dateTime': ts, 'rain': 0.0, 'rainRate': 0.0 }
            if ctr % 15 == 0:
                pkt['rain'] = 0.01
            ctr += 1
            user.rainrate.RainRate.add_packet(pkt, rain_entries)
            ts += 2

        self.assertEqual(len(rain_entries), 30)
        user.rainrate.RainRate.compute_rain_rate(pkt, rain_entries)
        self.assertEqual(pkt['rainRate'], 1.2)

    def test_compute_rain_rate_one_in_45(self):
        rain_entries = []
        ts = 1668104200

        ctr = 0
        for _ in range(1000):
            pkt = { 'dateTime': ts, 'rain': 0.0, 'rainRate': 0.0 }
            if ctr % 45 == 0:
                pkt['rain'] = 0.01
            ctr += 1
            user.rainrate.RainRate.add_packet(pkt, rain_entries)
            ts += 2

        self.assertEqual(len(rain_entries), 10)
        # One would expect 0.4, but 2 tips are sitting in the 2m bucket.
        # 3600 * 0.03 / 120 = 0.6
        user.rainrate.RainRate.compute_rain_rate(pkt, rain_entries)
        self.assertEqual(pkt['rainRate'], 0.6)


if __name__ == '__main__':
    unittest.main()
