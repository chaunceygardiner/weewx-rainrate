#    Copyright (c) 2022 John A Kline <john@johnkline.com>
#
#    See the file LICENSE.txt for your full rights.
#
"""Given two comma separated files, each containing a timestamp and a rainRate,
   match up the files and print <datetime>,<file-a-rainrate>,<file-b-rainrate>
   This program assumes 2s updates for the observations.  It will match records
   even if the observations' timestamps from each file are off by 1s.

    To Run:

        python bin/user/rate_computer/combiner.py tb3.csv tb7.csv

    Example output:
        .
        .
        .
        12/01/22 09:54:22,0.800,0.750
        12/01/22 09:54:24,0.800,0.750
        12/01/22 09:54:26,0.800,0.750
        12/01/22 09:54:28,0.800,0.750
        12/01/22 09:54:30,0.800,0.750
        12/01/22 09:54:32,0.800,0.750
        12/01/22 09:54:34,0.800,0.750
        12/01/22 09:54:36,0.800,0.750
        12/01/22 09:54:38,0.800,0.750
        12/01/22 09:54:40,0.800,0.750
        12/01/22 09:54:42,0.800,0.750
        12/01/22 09:54:44,0.800,0.750
        12/01/22 09:54:46,0.800,0.750
        12/01/22 09:54:48,0.800,0.750
        12/01/22 09:54:50,0.800,0.750
        12/01/22 09:54:52,0.800,1.090
        12/01/22 09:54:54,0.800,1.090
        12/01/22 09:54:56,0.800,1.090
        12/01/22 09:54:58,0.800,1.090
        .
        .
        .

"""

import datetime
import os
import sys

from dataclasses import dataclass
from typing import List

@dataclass
class RainEvent:
    """A list of RainEntry is kept for the last 15 minutes."""
    timestamp: int   # timestamp when this rain occurred
    rainRate : float # rainrate reported

class Combiner():
    @staticmethod
    def read_rain_events(rainfile: str) -> List[RainEvent]:
        rain_events: List[RainEvent] = []

        f = open(rainfile, "r")
        lines = f.readlines()
        for line in lines:
            cols = line.split(',')
            rain_events.append(RainEvent(
                timestamp = int(cols[0]),
                rainRate  = float(cols[1])))
        f.close()
        return rain_events


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print('usage %s <tb3_csv> <tb7_csv>')
        sys.exit(1)
    tb3_filename = sys.argv[1]
    tb7_filename = sys.argv[2]
    tb3 = Combiner.read_rain_events(tb3_filename)
    tb7 = Combiner.read_rain_events(tb7_filename)
    ts = min(tb3[0].timestamp, tb7[0].timestamp)
    i3 = 0
    i7 = 0
    print('Time,%s,%s' % (os.path.basename(tb3_filename).split('.')[0], os.path.basename(tb7_filename).split('.')[0]))
    while i3 < len(tb3) or i7 < len(tb7):
        if i3 != 0 and i3 < len(tb3) and tb3[i3 - 1].timestamp == tb3[i3].timestamp:
            # dup tb3 timestamp
            i3 += 1
        if i3 != 0 and i3 < len(tb3) - 1 and tb3[i3 - 1].timestamp == tb3[i3].timestamp - 1 and tb3[i3].timestamp == tb3[i3+1].timestamp - 1:
            # ignore one second jumps, if another one follows 1s later
            i3 += 1
        if i7 != 0 and i7 < len(tb7) - 1 and tb7[i7 - 1].timestamp == tb7[i7].timestamp - 1 and tb7[i7].timestamp == tb7[i7+1].timestamp - 1:
            # ignore one second jumps, if another one follows 1s later
            i7 += 1
        if i7 != 0 and i7 < len(tb7) and tb7[i7 - 1].timestamp == tb7[i7].timestamp:
            # dup tb7 timestamp
            i7 += 1
        if i3 >= len(tb3) and i7 >= len(tb7):
            continue
        if (i3 < len(tb3) and ts > (tb3[i3].timestamp + 1)) or (i7 < len(tb7) and ts > (tb7[i7].timestamp + 1)):
            print('Houston, we have a problem: ts:%s, tb3:%d, tb7:%d' % (datetime.datetime.fromtimestamp(ts).strftime('%m/%d/%y %H:%M:%S'), tb3[i3].timestamp, tb7[i7].timestamp))
            sys.exit(1)
        elif i3 < len(tb3) and i7 < len(tb7) and tb3[i3].timestamp >= ts - 1 and tb3[i3].timestamp <= ts + 1 and tb7[i7].timestamp >= ts - 1 and tb7[i7].timestamp <= ts + 1:
            # both timestamps match
            print('%s,%5.3f,%5.3f' % (datetime.datetime.fromtimestamp(ts).strftime('%m/%d/%y %H:%M:%S'), tb3[i3].rainRate, tb7[i7].rainRate))
            i3 += 1
            i7 += 1
        elif i3 < len(tb3) and tb3[i3].timestamp >= ts - 1 and tb3[i3].timestamp <= ts + 1:
            # tb3 matches
            # tb7 is missing because it is zero
            print('%s,%5.3f,0.0' % (datetime.datetime.fromtimestamp(ts).strftime('%m/%d/%y %H:%M:%S'), tb3[i3].rainRate))
            i3 += 1
        elif i7 < len(tb7) and tb7[i7].timestamp >= ts - 1 and tb7[i7].timestamp <= ts + 1:
            # tb7 matches
            # tb3 is missing because it is zero
            print('%s,0.0,%5.3f' % (datetime.datetime.fromtimestamp(ts).strftime('%m/%d/%y %H:%M:%S'), tb7[i7].rainRate))
            i7 += 1
        else:
            # both tb3 and tb7 are zero
            print('%s,0.0,0.0' % datetime.datetime.fromtimestamp(ts).strftime('%m/%d/%y %H:%M:%S'))
            # If ts > tb3 or tb5 timestamps, we have a problem
            if (i3 < len(tb3) and tb3[i3].timestamp < ts) or (i7 < len(tb7) and tb7[i7].timestamp < ts):
                print('SHOULD NOT GET HERE: Houston, we have a problem: ts:%d, tb3:%d, tb7:%d' % (ts, tb3[i3].timestamp, tb7[i7].timestamp))
                sys.exit(1)
        ts += 2
