# weewx-rainrate
*Open source plugin for WeeWX software.

Copyright (C)2022 by John A Kline (john@johnkline.com)

**This extension requires Python 3.7 or later and WeeWX 4.**


## Description

weewx-rainrate is a WeeWX service that attempts to produce a
"better" rainRate in loop packets.  It ignores any rainRate in the loop packet
by inserting(overwriting) rainRate to be the max of the
1 through 15m rain rate as computed by the extension.

## Why require Python 3.7 or later?

weewx-rainrate code includes type annotation which do not work with Python 2, nor in
earlier versions of Python 3.


## Licensing

weewx-rainrate is licensed under the GNU Public License v3.
