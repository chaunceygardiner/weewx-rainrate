# weewx-rainrate
*Open source plugin for WeeWX software.

Copyright (C)2022 by John A Kline (john@johnkline.com)

**This extension requires Python 3.7 or later and WeeWX 4.**


## Description

weewx-rainrate is a WeeWX service that attempts to produce a
"better" rainRate in loop packets.

The impetus for this extension is that author purchased a
high quality HyQuest Solutions TB3 siphoning rain gauge.
It is accurate to 2% at any rain intensity, but with the
siphon, two tips can come in quick succession.  As such
the rainRate produced by measuring the time delta between
two tips can be wildly overstated.

weewx-rainrate ignores the rainRate in the loop packet (if present)
by overwriting/inserting rainRate to be the max of the
1 through 15m rain rate as computed by the extension.

For low rain cases:

If there was just one bucket tip (in the first minute), we would see a rate of 0.6
selected (which is absurdly high).  As such, we'll only consider the 15m bucket
(rate of 0.04).

Similarly, for cases where only 0.02 has been observed in the last 15m, the
1-9m buckets will report unreasonably high rates, so zero them out.

Lasttly, for cases where 0.03 has been observed in the last 15m, zero out the
1-4m buckets.

## Why require Python 3.7 or later?

weewx-rainrate code includes type annotation which do not work with Python 2, nor in
earlier versions of Python 3.


## Licensing

weewx-rainrate is licensed under the GNU Public License v3.
