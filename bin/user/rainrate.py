"""
rainrate.py

Copyright (C)2020 by John A Kline (john@johnkline.com)
Distributed under the terms of the GNU Public License (GPLv3)

RainRate is a WeeWX service that inserts or overwrites rainRate
in loop packets to the he max of 5m through 15m rainRate calculations.
"""

import logging
import sys
import time
import random

from dataclasses import dataclass
from typing import Any, Dict, List

import weewx
import weewx.manager
import weeutil.logger


from weeutil.weeutil import timestamp_to_string
from weeutil.weeutil import to_bool
from weeutil.weeutil import to_int
from weewx.engine import StdService

# get a logger object
log = logging.getLogger(__name__)

RAIN24H_VERSION = '0.01'

if sys.version_info[0] < 3 or (sys.version_info[0] == 3 and sys.version_info[1] < 7):
    raise weewx.UnsupportedFeature(
        "weewx-rainrate requires Python 3.7 or later, found %s.%s" % (sys.version_info[0], sys.version_info[1]))

if weewx.__version__ < "4":
    raise weewx.UnsupportedFeature(
        "weewx-rainrate requires WeeWX, found %s" % weewx.__version__)

@dataclass
class RainEntry:
    timestamp: int
    amount   : float


class RainRate(StdService):
    def __init__(self, engine, config_dict):
        super(RainRate, self).__init__(engine, config_dict)
        log.info("Service version is %s." % RAIN24H_VERSION)

        if sys.version_info[0] < 3 or (sys.version_info[0] == 3 and sys.version_info[1] < 7):
            raise Exception("Python 3.7 or later is required for the rainrate plugin.")

        # Only continue if the plugin is enabled.
        rainrate_config_dict = config_dict.get('RainRate', {})
        enable = to_bool(rainrate_config_dict.get('enable'))
        if enable:
            log.info("RainRate is enabled...continuing.")
        else:
            log.info("RainRate is disabled. Enable it in the RainRate section of weewx.conf.")
            return

        self.total_rain: float = 0
        self.rain_entries : List[RainEntry] = []
        self.initialized = False

        self.bind(weewx.PRE_LOOP, self.pre_loop)
        self.bind(weewx.NEW_LOOP_PACKET, self.new_loop)

    def pre_loop(self, event):
        if self.initialized:
            return
        self.initialized = True

        try:
            binder = weewx.manager.DBBinder(self.config_dict)
            binding = self.config_dict.get('StdReport')['data_binding']
            dbm = binder.get_manager(binding)
            # Get the column names of the archive table.
            archive_columns: List[str] = dbm.connection.columnsOf('archive')

            # Get last n seconds of archive records.
            earliest_time: int = to_int(time.time()) - 900

            log.debug('Earliest time selected is %s' % timestamp_to_string(earliest_time))

            # Fetch the records.
            start = time.time()
            archive_pkts: List[Dict[str, Any]] = RainRate.get_archive_packets(
                dbm, archive_columns, earliest_time)

            # Save packets as appropriate.
            pkt_count = 0
            for pkt in archive_pkts:
                pkt_time = pkt['dateTime']
                fifteen_mins_later = pkt_time + 900
                if 'rain' in pkt and pkt['rain'] is not None and pkt['rain'] > 0.0:
                    self.total_rain += pkt['rain']
                    self.rain_entries.append(RainEntry(timestamp = fifteen_mins_later, amount = pkt['rain']))
                    pkt_count += 1
            log.debug('Collected %d archive packets containing rain in %f seconds.' % (pkt_count, time.time() - start))
        except Exception as e:
            # Print problem to log and give up.
            log.error('Error in RainRate setup.  RainRate is exiting. Exception: %s' % e)
            weeutil.logger.log_traceback(log.error, "    ****  ")

    @staticmethod
    def massage_near_zero(val: float)-> float:
        if val > -0.0000000001 and val < 0.0000000001:
            return 0.0
        else:
            return val

    @staticmethod
    def get_archive_packets(dbm, archive_columns: List[str],
            earliest_time: int) -> List[Dict[str, Any]]:
        packets = []
        for cols in dbm.genSql('SELECT * FROM archive' \
                ' WHERE dateTime > %d ORDER BY dateTime ASC' % earliest_time):
            pkt: Dict[str, Any] = {}
            for i in range(len(cols)):
                pkt[archive_columns[i]] = cols[i]
            packets.append(pkt)
            log.debug('get_archive_packets: pkt(%s): %s' % (
                timestamp_to_string(pkt['dateTime']), pkt))
        return packets

    def new_loop(self, event):
        pkt: Dict[str, Any] = event.packet
        pkt_time: int       = to_int(pkt['dateTime'])

        assert event.event_type == weewx.NEW_LOOP_PACKET
        log.debug(pkt)

        # Process new packet.
        # Be careful, the first time through, pkt['rain'] may be none.
        if 'rain' in pkt and pkt['rain'] is not None and pkt['rain'] > 0.0:
            pkt_time = pkt['dateTime']
            fifteen_mins_later = pkt_time + 900
            self.total_rain += pkt['rain']
            self.rain_entries.insert(0, RainEntry(timestamp = fifteen_mins_later, amount = pkt['rain']))
            log.debug('pkt_time: %d, found rain of %f, adding to total_rain.' % (pkt_time, pkt['rain']))

        # Debit and remove any entries that have matured.
        while len(self.rain_entries) > 0 and self.rain_entries[-1].timestamp <= pkt_time:
            del self.rain_entries[-1]

        # Add/update rainRate in packet
        # Compute 5-15m rainRates and report the largest rate.
        rainrates = [ 0.0 ] * 16 # cells 0, 1, 2, 3, 4 will remain 0.0 as we're only calculating 5-15.
        for entry in self.rain_entries:
            for minute in range(5, 16):
                if pkt_time - entry.timestamp < minute * 60:
                    rainrates[minute] += entry.amount
        for minute in range(5, 16):
            rainrates[minute] = 3600.0 * rainrates[minute] / (minute * 60)

        pkt['rainRate'] = max(rainrates)
        log.debug('new_loop(%d): raterates: %r' % (pkt['dateTime'], rainrates))
        log.debug('new_loop(%d): Added/updated pkt[rainRate] of %f' % (pkt['dateTime'], pkt['rainRate']))
