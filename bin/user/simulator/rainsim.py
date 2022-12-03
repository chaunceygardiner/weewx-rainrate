#    Copyright (c) 2022 John A Kline <john@johnkline.com>
#
#    See the file LICENSE.txt for your full rights.
#
"""Given a file of comma separated rain observations (timestamp,rain,rainRate),
   compute rain rates and print out, for each observation time,
   rain amount, original rain rate, the new computed rain rate.

    To Run:

        PYTHONPATH=/home/weewx/bin python bin/user/simulator/rainsim.py bin/user/simulator/2022Dec01_PaloAlto_0.68inch_storm_TB3.csv

    Example output:
Time                                 Rain  Orig. Rate Comp. Rate
------------------------------------ ----- ---------- ----------
2022-12-01 08:32:58 PST (1669912378)  0.00      0.000      0.000
2022-12-01 08:33:00 PST (1669912380)  0.00      0.000      0.000
2022-12-01 08:33:02 PST (1669912382)  0.00      0.000      0.000
.
.
.
2022-12-01 09:10:38 PST (1669914638)  0.00      0.060      0.040
2022-12-01 09:10:40 PST (1669914640)  0.00      0.060      0.040
2022-12-01 09:10:42 PST (1669914642)  0.00      0.060      0.040
2022-12-01 09:10:44 PST (1669914644)  0.00      0.060      0.040
2022-12-01 09:10:46 PST (1669914646)  0.00      0.060      0.040
2022-12-01 09:10:48 PST (1669914648)  0.00      0.060      0.040
2022-12-01 09:10:50 PST (1669914650)  0.00      0.060      0.040
2022-12-01 09:10:52 PST (1669914652)  0.00      0.060      0.040
2022-12-01 09:10:54 PST (1669914654)  0.00      0.060      0.040
2022-12-01 09:10:56 PST (1669914656)  0.00      0.060      0.040
2022-12-01 09:10:58 PST (1669914658)  0.00      0.060      0.040
2022-12-01 09:11:00 PST (1669914660)  0.00      0.060      0.040
2022-12-01 09:11:02 PST (1669914662)  0.00      0.060      0.040
2022-12-01 09:11:04 PST (1669914664)  0.00      0.060      0.040
2022-12-01 09:11:06 PST (1669914666)  0.00      0.060      0.040
2022-12-01 09:11:08 PST (1669914668)  0.00      0.060      0.040
2022-12-01 09:11:10 PST (1669914670)  0.02      0.060      0.180
2022-12-01 09:11:12 PST (1669914672)  0.00      0.060      0.180
2022-12-01 09:11:14 PST (1669914674)  0.00     15.570      0.180
2022-12-01 09:11:16 PST (1669914676)  0.00     15.570      0.180
2022-12-01 09:11:18 PST (1669914678)  0.00     15.570      0.180
2022-12-01 09:11:20 PST (1669914680)  0.00     15.570      0.180
2022-12-01 09:11:22 PST (1669914682)  0.00     15.570      0.180
2022-12-01 09:11:24 PST (1669914684)  0.00     15.570      0.180
2022-12-01 09:11:26 PST (1669914686)  0.00     15.570      0.180
2022-12-01 09:11:28 PST (1669914688)  0.00     15.570      0.180
2022-12-01 09:11:30 PST (1669914690)  0.00     15.570      0.180
2022-12-01 09:11:32 PST (1669914692)  0.00     15.570      0.180
2022-12-01 09:11:34 PST (1669914694)  0.00      1.060      0.180
2022-12-01 09:11:36 PST (1669914696)  0.00      1.060      0.180
2022-12-01 09:11:38 PST (1669914698)  0.00      1.060      0.180
2022-12-01 09:11:40 PST (1669914700)  0.00      1.060      0.180
2022-12-01 09:11:42 PST (1669914702)  0.00      1.060      0.180
2022-12-01 09:11:44 PST (1669914704)  0.00      0.810      0.180
2022-12-01 09:11:46 PST (1669914706)  0.00      0.810      0.180
2022-12-01 09:11:48 PST (1669914708)  0.00      0.810      0.180
2022-12-01 09:11:50 PST (1669914710)  0.00      0.810      0.180
2022-12-01 09:11:52 PST (1669914712)  0.00      0.810      0.180
2022-12-01 09:11:54 PST (1669914714)  0.00      0.810      0.180
2022-12-01 09:11:56 PST (1669914716)  0.00      0.650      0.180
2022-12-01 09:11:58 PST (1669914718)  0.00      0.650      0.180
2022-12-01 09:12:00 PST (1669914720)  0.00      0.650      0.180
2022-12-01 09:12:02 PST (1669914722)  0.00      0.650      0.180
2022-12-01 09:12:04 PST (1669914724)  0.00      0.650      0.180
2022-12-01 09:12:06 PST (1669914726)  0.00      0.550      0.180
2022-12-01 09:12:08 PST (1669914728)  0.00      0.550      0.180
2022-12-01 09:12:10 PST (1669914730)  0.00      0.550      0.180
2022-12-01 09:12:12 PST (1669914732)  0.00      0.550      0.180
2022-12-01 09:12:14 PST (1669914734)  0.00      0.550      0.180
2022-12-01 09:12:16 PST (1669914736)  0.00      0.470      0.180
2022-12-01 09:12:18 PST (1669914738)  0.00      0.470      0.180
2022-12-01 09:12:20 PST (1669914740)  0.00      0.470      0.180
2022-12-01 09:12:22 PST (1669914742)  0.00      0.470      0.180
2022-12-01 09:12:24 PST (1669914744)  0.00      0.470      0.180
.
.
.
"""

import logging
import sys

from dataclasses import dataclass
from typing import List

import weeutil.logger
from weeutil.weeutil import timestamp_to_string

import user.rainrate

log = logging.getLogger(__name__)

# Set up logging using the defaults.
weeutil.logger.setup('rainsim', {})

@dataclass
class RainEvent:
    """A list of RainEntry is kept for the last 15 minutes."""
    timestamp: int   # timestamp when this rain occurred
    rain     : float # amount of rain
    rainRate : float # rainrate reported

class RainSim():
    @staticmethod
    def read_rain_events(rainfile: str) -> List[RainEvent]:
        rain_events: List[RainEvent] = []

        f = open(rainfile, "r")
        lines = f.readlines()
        for line in lines:
            # 1669920114,0.0,15.16
            cols = line.split(',')
            rain_events.append(RainEvent(
                timestamp = int(cols[0]),
                rain      = float(cols[1]),
                rainRate  = float(cols[2])))
        return rain_events


if __name__ == '__main__':
    rain_events = RainSim.read_rain_events(sys.argv[1])
    rain_entries: List[user.rainrate.RainEntry] = []
    print('Time                                 Rain  Orig. Rate Comp. Rate')
    print('------------------------------------ ----- ---------- ----------')
    for event in rain_events:
        original_rainRate = event.rainRate
        pkt = { 'dateTime': event.timestamp, 'rain': event.rain, 'rainRate': event.rainRate }
        user.rainrate.RainRate.add_packet(pkt, rain_entries)
        user.rainrate.RainRate.compute_rain_rate(pkt, rain_entries)
        print('%s  %3.2f  %9.3f  %9.3f' % (timestamp_to_string(pkt['dateTime']), pkt['rain'], original_rainRate, pkt['rainRate']))
