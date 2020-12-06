import abc
import logging
import math
import struct
import time
import typing

import cc1101
import numpy

_MESSAGE_LENGTH_BITS = 65
_MESSAGE_REPEATS = 3


class Measurement(abc.ABC):
    # pylint: disable=too-few-public-methods
    @abc.abstractmethod
    def __str__(self) -> str:
        raise NotImplementedError()


class TemperatureMeasurement(Measurement):
    # pylint: disable=too-few-public-methods
    def __init__(self, *, degrees_celsius: float):
        self.degrees_celsius = degrees_celsius
        super().__init__()

    def __str__(self) -> str:
        return "temperature {:.02f}°C".format(self.degrees_celsius)


class RelativeHumidityMeasurement(Measurement):
    # pylint: disable=too-few-public-methods
    def __init__(self, value: float):
        assert 0 <= value <= 1, value
        self.value = value
        super().__init__()

    def __str__(self) -> str:
        return "relative humidity {:.01f}%".format(self.value * 100)


def _parse_message(
    bits
) -> typing.Tuple[TemperatureMeasurement, RelativeHumidityMeasurement]:
    assert bits.shape == (_MESSAGE_LENGTH_BITS,), bits.shape
    if (bits[:8] != 1).any():
        raise ValueError("invalid prefix in message: {}".format(bits))
    temperature_index, = struct.unpack(
        ">H", numpy.packbits(bits[32:44])  # , bitorder="big")
    )
    # advertised range: [-40°C, +60°C]
    # intercept: -40°C = -40°F
    # slope estimated with statsmodels.regression.linear_model.OLS
    # 12 bits have sufficient range: 2**12 * slope / 2**4 - 40 = 73.76
    temperature = TemperatureMeasurement(
        degrees_celsius=temperature_index / 576.077364 - 40
    )
    # advertised range: [10%, 99%]
    # intercept: 0%
    # slope estimated with statsmodels.regression.linear_model.OLS
    # 12 bits have sufficient range: 2**12 * slope / 2**4 + 0 = 1.27
    relative_humidity_index, = struct.unpack(
        ">H", numpy.packbits(bits[44:56])  # , bitorder="big")
    )
    relative_humidity = RelativeHumidityMeasurement(
        relative_humidity_index / 51451.432435
    )
    logging.debug(
        "undecoded prefix %s, %s, %s, undecoded suffix %s",
        numpy.packbits(bits[8:32]),  # address & battery?
        temperature,
        relative_humidity,
        bits[56:],  # checksum?
    )
    return (temperature, relative_humidity)


def _parse_transmission(
    signal: "numpy.ndarray(dtype=numpy.uint8)"
) -> typing.Tuple[TemperatureMeasurement, RelativeHumidityMeasurement]:
    bits = numpy.unpackbits(signal)[
        : _MESSAGE_LENGTH_BITS * _MESSAGE_REPEATS
    ]  # bitorder='big'
    repeats_bits = numpy.split(bits, _MESSAGE_REPEATS)
    # cc1101 might have skipped the first repeat
    if numpy.array_equal(repeats_bits[0], repeats_bits[1]) or numpy.array_equal(
        repeats_bits[0], repeats_bits[2]
    ):
        return _parse_message(repeats_bits[0])
    raise ValueError("repeats do not match")


def receive_ft017th_measurements() -> typing.Iterator[
    typing.Tuple[TemperatureMeasurement, RelativeHumidityMeasurement]
]:
    with cc1101.CC1101() as transceiver:
        transceiver.set_base_frequency_hertz(433.945e6)
        transceiver.set_symbol_rate_baud(2048)
        transceiver.set_sync_mode(
            cc1101.SyncMode.TRANSMIT_16_MATCH_15_BITS,
            _carrier_sense_threshold_enabled=True,
        )
        sync_word = bytes([255, 168])  # 168 might be sender-specific
        transceiver.set_sync_word(sync_word)
        transceiver.disable_checksum()
        transceiver.enable_manchester_code()
        transceiver.set_packet_length_mode(cc1101.PacketLengthMode.FIXED)
        transceiver.set_packet_length_bytes(
            math.ceil(_MESSAGE_LENGTH_BITS * _MESSAGE_REPEATS / 8) - len(sync_word)
        )
        transceiver._set_filter_bandwidth(mantissa=3, exponent=3)
        logging.debug(
            "%s, filter_bandwidth=%.0fkHz",
            transceiver,
            transceiver._get_filter_bandwidth_hertz() / 1000,
        )
        while True:
            transceiver._enable_receive_mode()
            time.sleep(0.05)
            while (
                transceiver.get_marc_state()
                == cc1101.MainRadioControlStateMachineState.RX
            ):
                time.sleep(8.0)
            packet = transceiver._get_received_packet()
            if packet:
                logging.debug("%s", packet)
                try:
                    yield _parse_transmission(
                        numpy.frombuffer(sync_word + packet.data, dtype=numpy.uint8)
                    )
                except ValueError:
                    logging.info("failed to decode %s", packet)


def _main():
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s:%(levelname)s:%(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z",
    )
    logging.getLogger("cc1101").setLevel(logging.INFO)
    for measurements in receive_ft017th_measurements():
        print(*measurements, sep="\t")


if __name__ == "__main__":
    _main()
