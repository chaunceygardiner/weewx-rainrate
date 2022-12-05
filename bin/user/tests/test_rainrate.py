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
        self.assertEqual(rain_entries[0], user.rainrate.RainEntry(expiration = ts + 1800, timestamp = ts, amount = 0.01))
        ts += 2

        # Add 448 pkts of zero rain.  Entry above should still be present.
        for _ in range(448):
            pkt = { 'dateTime': ts, 'rain': 0.00, 'rainRate': 0.0 }
            user.rainrate.RainRate.add_packet(pkt, rain_entries)
            ts += 2
        self.assertEqual(len(rain_entries), 1)
        self.assertEqual(rain_entries[0], user.rainrate.RainEntry(expiration = 1668104400 + 1800, timestamp = 1668104400, amount = 0.01))

        # Add a pkt of 0.01 rain.  Should now have two entries.
        pkt = { 'dateTime': ts, 'rain': 0.01, 'rainRate': 0.0 }
        user.rainrate.RainRate.add_packet(pkt, rain_entries)
        self.assertEqual(len(rain_entries), 2)
        self.assertEqual(rain_entries[0], user.rainrate.RainEntry(expiration = ts + 1800, timestamp = ts, amount = 0.01))
        self.assertEqual(rain_entries[1], user.rainrate.RainEntry(expiration = 1668104400 + 1800, timestamp = 1668104400, amount = 0.01))
        ts += 2

        # Add a pkt of 0.00 rain. Expect first entry to still be around.
        pkt = { 'dateTime': ts, 'rain': 0.00, 'rainRate': 0.0 }
        user.rainrate.RainRate.add_packet(pkt, rain_entries)
        self.assertEqual(len(rain_entries), 2)
        ts += 2

        # Add 449 more 0.00 rain packets.
        for _ in range(449):
            pkt = { 'dateTime': ts, 'rain': 0.00, 'rainRate': 0.0 }
            user.rainrate.RainRate.add_packet(pkt, rain_entries)
            ts += 2
        self.assertEqual(len(rain_entries), 2)

        # Add one more, expect only one entry in rain_entries.
        pkt = { 'dateTime': ts, 'rain': 0.00, 'rainRate': 0.0 }
        user.rainrate.RainRate.add_packet(pkt, rain_entries)
        ts += 2
        self.assertEqual(len(rain_entries), 1)

    def test_compute_rain_rate(self):
        rain_entries = []
        ts = 1668104200

        # A single tip. 0.01
        pkt = { 'dateTime': ts, 'rain': 0.01, 'rainRate': 0.0 }
        user.rainrate.RainRate.add_packet(pkt, rain_entries)
        user.rainrate.RainRate.compute_rain_rate(pkt, rain_entries)
        self.assertEqual(pkt['rainRate'], 0.0)

        # Another tip 2s later.  0.02 over 10m
        ts += 2
        pkt = { 'dateTime': ts, 'rain': 0.01, 'rainRate': 18.0 }
        user.rainrate.RainRate.add_packet(pkt, rain_entries)
        user.rainrate.RainRate.compute_rain_rate(pkt, rain_entries)
        # 0.01 in 2s is 18" an hour. 
        self.assertEqual(pkt['rainRate'], 18.0)

        # Another tip 2s later.
        ts += 2
        pkt = { 'dateTime': 1668104204, 'rain': 0.01, 'rainRate': 18.0 }
        user.rainrate.RainRate.add_packet(pkt, rain_entries)
        user.rainrate.RainRate.compute_rain_rate(pkt, rain_entries)
        # Still an 18s rain rate.
        self.assertEqual(pkt['rainRate'], 18.0)

        # Another tip 2s later.  0.04 over 4m
        ts += 2
        pkt = { 'dateTime': ts, 'rain': 0.01, 'rainRate': 18.0 }
        user.rainrate.RainRate.add_packet(pkt, rain_entries)
        user.rainrate.RainRate.compute_rain_rate(pkt, rain_entries)
        self.assertEqual(pkt['rainRate'], 18.0)

        # No tip for 112s
        for _ in range(0, 112, 2):
            ts += 2
            pkt = { 'dateTime': ts, 'rain': 0.00, 'rainRate': 99.9 }
            user.rainrate.RainRate.add_packet(pkt, rain_entries)
            user.rainrate.RainRate.compute_rain_rate(pkt, rain_entries)
        # Previous tip was 114s ago.
        self.assertAlmostEqual(pkt['rainRate'], 0.31578947368)

        # Another tip 2s later.
        ts += 2
        pkt = { 'dateTime': ts, 'rain': 0.01, 'rainRate': 99.9 }
        user.rainrate.RainRate.add_packet(pkt, rain_entries)
        user.rainrate.RainRate.compute_rain_rate(pkt, rain_entries)
        # Previous tip also was 114s ago.
        self.assertAlmostEqual(pkt['rainRate'], 0.31578947368)

    def test_compute_rain_rate2(self):
        rain_entries = []
        ts = 1668104200

        # A 0.02 in one pkt.
        pkt = { 'dateTime': ts, 'rain': 0.02, 'rainRate': 0.0 }
        user.rainrate.RainRate.add_packet(pkt, rain_entries)
        user.rainrate.RainRate.compute_rain_rate(pkt, rain_entries)
        # 0.02 split.  0.01 900s ago, 0.01 now
        # That's 0.01 since previous tip 900s ago
        self.assertEqual(pkt['rainRate'], 0.04)

        # Another tip 0.02 2s later.
        ts += 2
        pkt = { 'dateTime': ts, 'rain': 0.02, 'rainRate': 18.0 }
        user.rainrate.RainRate.add_packet(pkt, rain_entries)
        user.rainrate.RainRate.compute_rain_rate(pkt, rain_entries)
        # Now we have a tip now and the previous tip is 1s ago!
        self.assertEqual(pkt['rainRate'], 36.0)

        # No rain for 4:56
        for _ in range(148):
            ts += 2
            pkt = { 'dateTime': ts, 'rain': 0.0, 'rainRate': 18.0 }
            user.rainrate.RainRate.add_packet(pkt, rain_entries)
        user.rainrate.RainRate.compute_rain_rate(pkt, rain_entries)
        # Prvious tip was 297s ago.
        self.assertAlmostEqual(pkt['rainRate'], 0.12121212121)

        # No rain for 5:00
        for _ in range(150):
            ts += 2
            pkt = { 'dateTime': ts, 'rain': 0.0, 'rainRate': 18.0 }
            user.rainrate.RainRate.add_packet(pkt, rain_entries)
        # Prvious tip was 597s ago.
        user.rainrate.RainRate.compute_rain_rate(pkt, rain_entries)
        self.assertAlmostEqual(pkt['rainRate'], 0.06030150753)

        # No rain for 5:00
        for _ in range(150):
            ts += 2
            pkt = { 'dateTime': ts, 'rain': 0.0, 'rainRate': 18.0 }
            user.rainrate.RainRate.add_packet(pkt, rain_entries)
        # Prvious tip was 897s ago.
        user.rainrate.RainRate.compute_rain_rate(pkt, rain_entries)
        self.assertAlmostEqual(pkt['rainRate'], 0.04013377926)

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

        # 2000 seconds of packets, but we only keep 1800s of entries.
        # Rain every 4s is 450 entries.
        self.assertEqual(len(rain_entries), 450)
        user.rainrate.RainRate.compute_rain_rate(pkt, rain_entries)
        # Prevous tip was 6s ago.
        self.assertEqual(pkt['rainRate'], 6.0)

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

        # 1800s, rain every 30s
        self.assertEqual(len(rain_entries), 60)
        user.rainrate.RainRate.compute_rain_rate(pkt, rain_entries)
        # Prevous packet 32s ago.
        self.assertAlmostEqual(pkt['rainRate'], 0.75)

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

        # 1800s / 90 = 20
        self.assertEqual(len(rain_entries), 20)
        # Previous tip was 108s ago.
        user.rainrate.RainRate.compute_rain_rate(pkt, rain_entries)
        # Prevous tip was 90s ago.
        self.assertAlmostEqual(pkt['rainRate'], 0.33333333333)

    def test_2022_11_rain_event(self):
        """
        "2022-11-06 01:05:00",1667696700,0.01,0.0
        ...
        "2022-11-09 22:40:00",1668033600,0.01,0.0
        """
        rain_entries = []
        infile = open('bin/user/tests/2022-11-rain-event.csv', 'r')
        lines = infile.readlines()
        infile.close()
        highRainRate = 0.0
        for line in lines:
            cols = line.split(',')
            ts       = int(cols[1])
            rain     = float(cols[2])
            rainRate = float(cols[3])
            pkt = { 'dateTime': ts, 'rain': rain, 'rainRate': rainRate }
            user.rainrate.RainRate.add_packet(pkt, rain_entries)
            user.rainrate.RainRate.compute_rain_rate(pkt, rain_entries)
            if pkt['rainRate'] > highRainRate:
                highRainRate = pkt['rainRate']
        self.assertAlmostEqual(highRainRate, 0.48)


if __name__ == '__main__':
    unittest.main()
