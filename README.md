# weewx-rainrate
*Open source plugin for WeeWX software.

Copyright (C)2022 by John A Kline (john@johnkline.com)

**This extension requires Python 3.7 or later and WeeWX 4.**


## Description

weewx-rainrate is a WeeWX service that attempts to produce a
"better" rainRate in loop packets.  It is intened to be used
for tipping rain gauges that use a siphon for better accuracy
over a wide range of rainfall.  These professional gauges
maintain their accuracy over a wide range of rain intensity,
but are unsuitable for computing rain rain via the time
between two tips.  The reason or the unsuitability is that
a single discharge of the siphon my result in multiple tips
(in close sucession).  The result of two tips in close
succession will be wildly overstated rain rate.

The impetus for this extension was the author's purchase of a
professional HyQuest Solutions TB3 tipping rain gauge with
siphon.  It is accurate to 2% at any rain intensity, but with
the siphon, two tips can come in quick succession.

weewx-rainrate ignores the rainRate in the loop packet (if present)
by overwriting/inserting rainRate to be the max of the
3 through 15m rain rate (in 30s increments)  as computed by the extension.

## Algorithm

For cases where at least 0.04 (4 tips) of rain have occurred in the last
15 minutes, rain for the 3m-15m time periods (in 30s increments) is
is compiled, a rain rate is computed for each, and the largest rate is chosen.
Rain rates are rounded to three decimals.

### Example

0.01 rain    43s ago.
0.01 rain  3:12m ago.
0.01 rain  6:31m ago.
0.01 rain 14:10m ago.

The following table is computed and a 0.343 rainrate will be
reported (the highest rate is the 0:00-3:30m bucket).

| Bucket             | Timespan |    Rain     |  Rate/hr. |
|--------------------|---------:|------------:|----------:|
|  0:00m -  3:00m    |     180s |        0.01 |     0.200 |
| __0:00m -  3:30m__ |  __210s__|     __0.02__|  __0.343__|
|   0:00m -  4:00m   |     240s |        0.02 |     0.300 |
|   0:00m -  4:30m   |     270s |        0.02 |     0.267 |
|   0:00m -  5:00m   |     300s |        0.02 |     0.240 |
|   0:00m -  5:30m   |     330s |        0.02 |     0.218 |
|   0:00m -  6:00m   |     360s |        0.02 |     0.200 |
|   0:00m -  6:30m   |     390s |        0.02 |     0.185 |
|   0:00m -  7:00m   |     420s |        0.03 |     0.257 |
|   0:00m -  7:30m   |     450s |        0.03 |     0.240 |
|   0:00m -  8:00m   |     480s |        0.03 |     0.225 |
|   0:00m -  8:30m   |     510s |        0.03 |     0.212 |
|   0:00m -  9:00m   |     540s |        0.03 |     0.200 |
|   0:00m -  9:30m   |     570s |        0.03 |     0.189 |
|   0:00m - 10:00m   |     600s |        0.03 |     0.180 |
|   0:00m - 10:30m   |     630s |        0.03 |     0.171 |
|   0:00m - 11:00m   |     660s |        0.03 |     0.164 |
|   0:00m - 11:30m   |     690s |        0.03 |     0.157 |
|   0:00m - 12:00m   |     720s |        0.03 |     0.150 |
|   0:00m - 12:30m   |     750s |        0.03 |     0.144 |
|   0:00m - 13:00m   |     780s |        0.03 |     0.138 |
|   0:00m - 13:30m   |     810s |        0.03 |     0.133 |
|   0:00m - 14:00m   |     840s |        0.03 |     0.129 |
|   0:00m - 14:30m   |     870s |        0.04 |     0.166 |
|   0:00m - 15:00m   |     900s |        0.04 |     0.160 |

## Algorithm for Smaller Volumes of Rain

For low rain cases (< 0.04 in last 15m):

For cases where 0.01 is observed in the last 15m, no matter when in that 15m
the tip occurred, only the 15m bucket is considered (hence, a rate of 0.04).

Similarly, for cases where only 0.02 has been observed in the last 15m, only
the 10m through 15m buckets are considered.

Lasttly, for cases where 0.03 has been observed in the last 15m, only
the 5m-15m buckets are considered.

## Why require Python 3.7 or later?

weewx-rainrate code includes type annotation which do not work with Python 2, nor in
earlier versions of Python 3.

# Installation Instructions

1. Download the lastest release, weewx-rainrate-0.12.zip, from the
   [GitHub Repository](https://github.com/chaunceygardiner/weewx-rainrate).

1. Run the following command.

   `sudo /home/weewx/bin/wee_extension --install weewx-rainrate-0.12.zip`

   Note: this command assumes weewx is installed in /home/weewx.  If it's installed
   elsewhere, adjust the path of wee_extension accordingly.

1. Restart WeeWX.

1. The following entry is created in `weewx.conf`.  To disable `weewx-rainrate` without
   uninstalling it, change the enable line to false.
```
[RainRate]
    enable = true
```

## Licensing

weewx-rainrate is licensed under the GNU Public License v3.
