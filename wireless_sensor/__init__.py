# wireless-sensor - Receive & decode signals of FT017TH wireless thermo/hygrometers
#
# Copyright (C) 2020 Fabian Peter Hammerle <fabian@hammerle.me>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import abc
import collections
import datetime
import logging
import math
import struct
import sys
import time
import typing

import cc1101
import numpy

_LOGGER = logging.getLogger(__name__)

Measurement = collections.namedtuple(
    "Measurement",
    ["decoding_timestamp", "temperature_degrees_celsius", "relative_humidity"],
)


class _UnexpectedPacketLengthError(ValueError):
    pass


class DecodeError(ValueError):
    pass


def _now_local() -> datetime.datetime:  # pragma: no cover
    if sys.version_info < (3, 6):
        return datetime.datetime.now(tz=datetime.timezone.utc).astimezone()
    return datetime.datetime.now().astimezone()


class FT017TH:

    # pylint: disable=too-few-public-methods

    _MESSAGE_LENGTH_BITS = 65
    _MESSAGE_REPEATS = 3

    @classmethod
    def _parse_message(cls, bits) -> Measurement:
        assert bits.shape == (cls._MESSAGE_LENGTH_BITS,), bits.shape
        if (bits[:8] != 1).any():
            raise DecodeError("invalid prefix in message: {}".format(bits))
        (temperature_index,) = struct.unpack(
            ">H", numpy.packbits(bits[32:44])  # , bitorder="big")
        )
        # advertised range: [-40°C, +60°C]
        # intercept: -40°C = -40°F
        # slope estimated with statsmodels.regression.linear_model.OLS
        # 12 bits have sufficient range: 2**12 * slope / 2**4 - 40 = 73.76
        temperature_degrees_celsius = temperature_index / 576.077364 - 40
        # advertised range: [10%, 99%]
        # intercept: 0%
        # slope estimated with statsmodels.regression.linear_model.OLS
        # 12 bits have sufficient range: 2**12 * slope / 2**4 + 0 = 1.27
        (relative_humidity_index,) = struct.unpack(
            ">H", numpy.packbits(bits[44:56])  # , bitorder="big")
        )
        relative_humidity = relative_humidity_index / 51451.432435
        _LOGGER.debug(
            "undecoded prefix %s, %.02f°C, %.01f%%, undecoded suffix %s",
            numpy.packbits(bits[8:32]),  # address & battery?
            temperature_degrees_celsius,
            relative_humidity * 100,
            bits[56:],  # checksum?
        )
        return Measurement(
            decoding_timestamp=_now_local(),
            temperature_degrees_celsius=temperature_degrees_celsius,
            relative_humidity=relative_humidity,
        )

    @classmethod
    def _parse_transmission(
        cls, signal: numpy.ndarray  # dtype=numpy.uint8
    ) -> Measurement:
        bits = numpy.unpackbits(signal)[
            : cls._MESSAGE_LENGTH_BITS * cls._MESSAGE_REPEATS
        ]  # bitorder='big'
        repeats_bits = numpy.split(bits, cls._MESSAGE_REPEATS)
        # cc1101 might have skipped the first repeat
        if numpy.array_equal(repeats_bits[0], repeats_bits[1]) or numpy.array_equal(
            repeats_bits[0], repeats_bits[2]
        ):
            return cls._parse_message(repeats_bits[0])
        raise DecodeError("repeats do not match")

    _SYNC_WORD = bytes([255, 168])  # 168 might be sender-specific

    def __init__(self):
        self._transceiver = cc1101.CC1101(lock_spi_device=True)
        self._transmission_length_bytes = math.ceil(
            self._MESSAGE_LENGTH_BITS * self._MESSAGE_REPEATS / 8
        ) - len(self._SYNC_WORD)

    def _configure_transceiver(self):
        self._transceiver.set_base_frequency_hertz(433.945e6)
        self._transceiver.set_symbol_rate_baud(2048)
        self._transceiver.set_sync_mode(
            cc1101.SyncMode.TRANSMIT_16_MATCH_15_BITS,
            _carrier_sense_threshold_enabled=True,
        )
        self._transceiver.set_sync_word(self._SYNC_WORD)
        self._transceiver.disable_checksum()
        self._transceiver.enable_manchester_code()
        self._transceiver.set_packet_length_mode(cc1101.PacketLengthMode.FIXED)
        self._transceiver.set_packet_length_bytes(self._transmission_length_bytes)
        # pylint: disable=protected-access; version pinned
        self._transceiver._set_filter_bandwidth(mantissa=3, exponent=3)

    def _receive_packet(
        self,
    ) -> typing.Optional[
        cc1101._ReceivedPacket  # pylint: disable=protected-access; version pinned
    ]:
        self._transceiver._enable_receive_mode()  # pylint: disable=protected-access; version pinned
        time.sleep(0.05)
        while (
            self._transceiver.get_marc_state()
            == cc1101.MainRadioControlStateMachineState.RX
        ):
            time.sleep(8.0)  # transmits approx once per minute
        return (
            # pylint: disable=protected-access; version pinned
            self._transceiver._get_received_packet()
        )

    def _receive_measurement(self) -> typing.Optional[Measurement]:
        packet = self._receive_packet()
        if not packet:
            return None
        signal = numpy.frombuffer(self._SYNC_WORD + packet.data, dtype=numpy.uint8)
        if signal.shape != (self._transmission_length_bytes,):
            raise _UnexpectedPacketLengthError()
        try:
            return self._parse_transmission(signal)
        except DecodeError as exc:
            _LOGGER.debug("failed to decode %s: %s", packet, str(exc), exc_info=exc)
        return None

    _LOCK_WAIT_START_SECONDS = 2
    _LOCK_WAIT_FACTOR = 2

    def receive(self) -> typing.Iterator[Measurement]:
        lock_wait_seconds = self._LOCK_WAIT_START_SECONDS
        while True:
            try:
                with self._transceiver:
                    self._configure_transceiver()
                    _LOGGER.debug(
                        "%s, filter_bandwidth=%.0fkHz",
                        self._transceiver,
                        # pylint: disable=protected-access; version pinned
                        self._transceiver._get_filter_bandwidth_hertz() / 1000,
                    )
                    while True:
                        measurement = self._receive_measurement()
                        if measurement:
                            yield measurement
                            lock_wait_seconds = self._LOCK_WAIT_START_SECONDS
            except _UnexpectedPacketLengthError:
                _LOGGER.info(
                    "unexpected packet length;"
                    " reconfiguring as transceiver was potentially accessed by another process"
                )
            except BlockingIOError:
                _LOGGER.info("SPI device locked, waiting %d seconds", lock_wait_seconds)
                time.sleep(lock_wait_seconds)
                lock_wait_seconds *= self._LOCK_WAIT_FACTOR
