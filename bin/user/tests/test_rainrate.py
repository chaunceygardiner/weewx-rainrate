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
        self.assertEqual(rain_entries[0], user.rainrate.RainEntry(expiration = ts + 1800, timestamp = ts, amount = 0.01, dont_merge = False))
        ts += 2

        # Add 448 pkts of zero rain.  Entry above should still be present.
        for _ in range(448):
            pkt = { 'dateTime': ts, 'rain': 0.00, 'rainRate': 0.0 }
            user.rainrate.RainRate.add_packet(pkt, rain_entries)
            ts += 2
        self.assertEqual(len(rain_entries), 1)
        self.assertEqual(rain_entries[0], user.rainrate.RainEntry(expiration = 1668104400 + 1800, timestamp = 1668104400, amount = 0.01, dont_merge = False))

        # Add a pkt of 0.01 rain.  Should now have two entries.
        pkt = { 'dateTime': ts, 'rain': 0.01, 'rainRate': 0.0 }
        user.rainrate.RainRate.add_packet(pkt, rain_entries)
        self.assertEqual(len(rain_entries), 2)
        self.assertEqual(rain_entries[0], user.rainrate.RainEntry(expiration = ts + 1800, timestamp = ts, amount = 0.01, dont_merge = False))
        self.assertEqual(rain_entries[1], user.rainrate.RainEntry(expiration = 1668104400 + 1800, timestamp = 1668104400, amount = 0.01, dont_merge = False))
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


    def test_archive_records_to_rain_entries(self):
        archive_interval = 300

        rain_entries = []
        rec = { 'dateTime': 1673208000, 'usUnits': 'US', 'rain': 0.05, 'rainRate': 0.60 }
        user.rainrate.RainRate.archive_records_to_rain_entries(rec, archive_interval, rain_entries)
        self.assertEqual(len(rain_entries), 5)

        self.assertEqual(rain_entries[4].timestamp, 1673207700)
        self.assertAlmostEqual(rain_entries[4].amount, 0.01)
        self.assertAlmostEqual(rain_entries[4].expiration, 1673209500)

        self.assertEqual(rain_entries[3].timestamp, 1673207760)
        self.assertAlmostEqual(rain_entries[3].amount, 0.01)
        self.assertAlmostEqual(rain_entries[3].expiration, 1673209560)

        self.assertEqual(rain_entries[2].timestamp, 1673207820)
        self.assertAlmostEqual(rain_entries[2].amount, 0.01)
        self.assertAlmostEqual(rain_entries[2].expiration, 1673209620)

        self.assertEqual(rain_entries[1].timestamp, 1673207880)
        self.assertAlmostEqual(rain_entries[1].amount, 0.01)
        self.assertAlmostEqual(rain_entries[1].expiration, 1673209680)

        self.assertEqual(rain_entries[0].timestamp, 1673207940)
        self.assertAlmostEqual(rain_entries[0].amount, 0.01)
        self.assertAlmostEqual(rain_entries[0].expiration, 1673209740)

        rain_entries = []
        rec = { 'dateTime': 1673208000, 'usUnits': 'US', 'rain': 0.01, 'rainRate': 0.60 }
        user.rainrate.RainRate.archive_records_to_rain_entries(rec, archive_interval, rain_entries)
        self.assertEqual(len(rain_entries), 1)

        self.assertEqual(rain_entries[0].timestamp, 1673207850)
        self.assertAlmostEqual(rain_entries[0].amount, 0.01)
        self.assertAlmostEqual(rain_entries[0].expiration, 1673209650)

        rain_entries = []
        rec = { 'dateTime': 1673208000, 'usUnits': 'US', 'rain': 0.02, 'rainRate': 0.60 }
        user.rainrate.RainRate.archive_records_to_rain_entries(rec, archive_interval, rain_entries)
        self.assertEqual(len(rain_entries), 2)

        self.assertEqual(rain_entries[1].timestamp, 1673207700)
        self.assertAlmostEqual(rain_entries[1].amount, 0.01)
        self.assertAlmostEqual(rain_entries[1].expiration, 1673209500)

        self.assertEqual(rain_entries[0].timestamp, 1673207850)
        self.assertAlmostEqual(rain_entries[0].amount, 0.01)
        self.assertAlmostEqual(rain_entries[0].expiration, 1673209650)


    def test_compute_rain_rate(self):
        rain_entries = []
        ts = 1668104200

        # A single tip. 0.01
        pkt = { 'dateTime': ts, 'rain': 0.01, 'rainRate': 0.0 }
        user.rainrate.RainRate.add_packet(pkt, rain_entries)
        user.rainrate.RainRate.compute_rain_rate(pkt, rain_entries)
        self.assertEqual(pkt['rainRate'], 0.0)

        # Another tip 2s later.  These will be treated as a double tip and merged.
        # Since that make it the first tip of the storm, rain rate is 0.0.
        ts += 2
        pkt = { 'dateTime': ts, 'rain': 0.01, 'rainRate': 0.0 }
        user.rainrate.RainRate.add_packet(pkt, rain_entries)
        user.rainrate.RainRate.compute_rain_rate(pkt, rain_entries)
        # 0.01 in 2s is 18" an hour.
        self.assertEqual(pkt['rainRate'], 0.0)

        # Another tip 2s later.
        ts += 2
        pkt = { 'dateTime': 1668104204, 'rain': 0.01, 'rainRate': 0.0 }
        user.rainrate.RainRate.add_packet(pkt, rain_entries)
        user.rainrate.RainRate.compute_rain_rate(pkt, rain_entries)
        # Still an 18s rain rate.
        self.assertEqual(pkt['rainRate'], 18.0)

        # Another tip 2s later.
        ts += 2
        pkt = { 'dateTime': ts, 'rain': 0.01, 'rainRate': 0.0 }
        user.rainrate.RainRate.add_packet(pkt, rain_entries)
        user.rainrate.RainRate.compute_rain_rate(pkt, rain_entries)
        self.assertEqual(pkt['rainRate'], 18.0)

        # Another tip 2s later.
        ts += 2
        pkt = { 'dateTime': ts, 'rain': 0.01, 'rainRate': 0.0 }
        user.rainrate.RainRate.add_packet(pkt, rain_entries)
        user.rainrate.RainRate.compute_rain_rate(pkt, rain_entries)
        self.assertEqual(pkt['rainRate'], 18.0)

        # Another tip 4s later.
        ts += 4
        pkt = { 'dateTime': ts, 'rain': 0.01, 'rainRate': 0.0 }
        user.rainrate.RainRate.add_packet(pkt, rain_entries)
        user.rainrate.RainRate.compute_rain_rate(pkt, rain_entries)
        self.assertEqual(pkt['rainRate'], 9.0)

        # No tip for 112s
        for _ in range(0, 112, 2):
            ts += 2
            pkt = { 'dateTime': ts, 'rain': 0.00, 'rainRate': 99.9 }
            user.rainrate.RainRate.add_packet(pkt, rain_entries)
            user.rainrate.RainRate.compute_rain_rate(pkt, rain_entries)
        # Previous tip was 114s ago.
        self.assertAlmostEqual(pkt['rainRate'], 0.32142857142857145)

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
        # It's still a first tip (even if it was 2), so no rain rate.
        self.assertEqual(pkt['rainRate'], 0.0)

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
        # Previous tip was 297s ago.
        self.assertAlmostEqual(pkt['rainRate'], 0.12162162162162163)

        # No rain for 5:00
        for _ in range(150):
            ts += 2
            pkt = { 'dateTime': ts, 'rain': 0.0, 'rainRate': 18.0 }
            user.rainrate.RainRate.add_packet(pkt, rain_entries)
        # Previous tip was 597s ago.
        user.rainrate.RainRate.compute_rain_rate(pkt, rain_entries)
        self.assertAlmostEqual(pkt['rainRate'], 0.06040268456375839)

        # No rain for 5:00
        for _ in range(150):
            ts += 2
            pkt = { 'dateTime': ts, 'rain': 0.0, 'rainRate': 18.0 }
            user.rainrate.RainRate.add_packet(pkt, rain_entries)
        # Previous tip was 897s ago.
        user.rainrate.RainRate.compute_rain_rate(pkt, rain_entries)
        self.assertAlmostEqual(pkt['rainRate'], 0.04017857142857143)

        # No rain for 20:00
        for _ in range(600):
            ts += 2
            pkt = { 'dateTime': ts, 'rain': 0.0, 'rainRate': 18.0 }
            user.rainrate.RainRate.add_packet(pkt, rain_entries)
        # Previous tip was 2097s ago.
        user.rainrate.RainRate.compute_rain_rate(pkt, rain_entries)
        self.assertAlmostEqual(pkt['rainRate'], 0.0)

        # Add a tip
        ts += 2
        pkt = { 'dateTime': ts, 'rain': 0.1, 'rainRate': 18.0 }
        user.rainrate.RainRate.add_packet(pkt, rain_entries)
        user.rainrate.RainRate.compute_rain_rate(pkt, rain_entries)
        self.assertAlmostEqual(pkt['rainRate'], 0.0)

        # Add a triple tip in 30s
        ts += 30
        pkt = { 'dateTime': ts, 'rain': 0.03, 'rainRate': 18.0 }
        user.rainrate.RainRate.add_packet(pkt, rain_entries)
        user.rainrate.RainRate.compute_rain_rate(pkt, rain_entries)
        # Expect 1 tip 30s ago, 1 tip 20s ago, 1 tip 10s ago, 1 tip now
        # A tip in 10s is 360 tips an hour or 3.6" rain rate
        self.assertAlmostEqual(pkt['rainRate'], 3.6)


    def test_consecutive_packet_tips(self):
        rain_entries = []
        ts = 1668104200

        # A single tip. 0.01
        pkt = { 'dateTime': ts, 'rain': 0.01, 'rainRate': 0.0 }
        user.rainrate.RainRate.add_packet(pkt, rain_entries)
        user.rainrate.RainRate.compute_rain_rate(pkt, rain_entries)
        self.assertEqual(pkt['rainRate'], 0.0)

        # Another tip 30s later.
        ts += 30
        pkt = { 'dateTime': ts, 'rain': 0.01, 'rainRate': 0.0 }
        user.rainrate.RainRate.add_packet(pkt, rain_entries)
        user.rainrate.RainRate.compute_rain_rate(pkt, rain_entries)
        # 0.01 in 30s is 1.2" an hour.
        self.assertEqual(pkt['rainRate'], 1.2)

        # Another tip in the next loop packet.
        ts += 2
        pkt = { 'dateTime': ts, 'rain': 0.01, 'rainRate': 0.0 }
        user.rainrate.RainRate.add_packet(pkt, rain_entries)
        user.rainrate.RainRate.compute_rain_rate(pkt, rain_entries)
        # We expect the last two rain events to be combined and then equally distributed from previous tip
        # 32s ago: 0.01
        # 16s ago: 0.01
        # now    : 0.01
        # 0.01 in 16s is 2.25"/hr.
        self.assertEqual(pkt['rainRate'], 2.25)

        # A single tip 10s later
        ts += 10
        pkt = { 'dateTime': ts, 'rain': 0.01, 'rainRate': 0.0 }
        user.rainrate.RainRate.add_packet(pkt, rain_entries)
        user.rainrate.RainRate.compute_rain_rate(pkt, rain_entries)
        self.assertEqual(pkt['rainRate'], 3.6)

        # Another tip in the next loop packet.
        ts += 2
        pkt = { 'dateTime': ts, 'rain': 0.01, 'rainRate': 0.0 }
        user.rainrate.RainRate.add_packet(pkt, rain_entries)
        user.rainrate.RainRate.compute_rain_rate(pkt, rain_entries)
        # We expect the last two rain events to be combined and then equally distributed from previous tip
        # 12s ago: 0.01
        # 6s  ago: 0.01
        # now    : 0.01
        # 0.01 in 6s is 6.0"/hr.
        self.assertEqual(pkt['rainRate'], 6.0)


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

        # 2000 seconds of packets.
        # Rain every 4s.
        self.assertEqual(len(rain_entries), 450)
        user.rainrate.RainRate.compute_rain_rate(pkt, rain_entries)
        # Prevous tip was 6s ago.
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

        # 1800s, rain every 30s
        self.assertEqual(len(rain_entries), 60)
        user.rainrate.RainRate.compute_rain_rate(pkt, rain_entries)
        # Prevous packet 32s ago.
        self.assertAlmostEqual(pkt['rainRate'], 1.2)

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
        self.assertAlmostEqual(pkt['rainRate'], 0.4)

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
