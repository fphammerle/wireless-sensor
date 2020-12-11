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

import datetime
import logging
import queue
import unittest.mock

import cc1101
import numpy
import pytest

import wireless_sensor

# pylint: disable=protected-access


@pytest.mark.parametrize(
    ("bits", "temperature_degrees_celsius", "relative_humidity"),
    [
        (
            "11111111101010001011001100100000100100000000010111101111001000011",
            23.99,
            0.472,
        ),
        (
            "11111111101010001011001100100000100011111110010111101100010000011",
            23.94,
            0.471,
        ),
    ],
)
def test__parse_message(bits, temperature_degrees_celsius, relative_humidity):
    measurement = wireless_sensor.FT017TH._parse_message(
        numpy.array([int(b) for b in bits], dtype=numpy.uint8)
    )
    assert measurement.decoding_timestamp.tzinfo is not None
    assert (
        datetime.datetime.now(tz=datetime.timezone.utc) - measurement.decoding_timestamp
    ).total_seconds() < 1
    assert measurement.temperature_degrees_celsius == pytest.approx(
        temperature_degrees_celsius, abs=0.01
    )
    assert measurement.relative_humidity == pytest.approx(relative_humidity, abs=0.001)


@pytest.mark.parametrize(
    "bits", ["11101111101010001011001100100000100011111110010111101100010000011"]
)
def test__parse_message_invalid_prefix(bits):
    with pytest.raises(wireless_sensor.DecodeError, match=r"\binvalid prefix\b"):
        wireless_sensor.FT017TH._parse_message(
            numpy.array([int(b) for b in bits], dtype=numpy.uint8)
        )


@pytest.mark.parametrize(
    ("signal", "message_bits"),
    [
        (
            b"\xff\xa8\xb3 \x90\x05\xef!\xff\xd4Y\x90H"
            b"\x02\xf7\x90\xff\xff\xff\xff\xff\xff\xff\xff\xff",
            "11111111101010001011001100100000100100000000010111101111001000011",
        )
    ],
)
def test__parse_transmission(signal, message_bits):
    with unittest.mock.patch(
        "wireless_sensor.FT017TH._parse_message"
    ) as parse_message_mock:
        wireless_sensor.FT017TH._parse_transmission(
            numpy.frombuffer(signal, dtype=numpy.uint8)
        )
    # .assert_called_once() was added in python3.6
    assert parse_message_mock.call_count == 1
    args, kwargs = parse_message_mock.call_args
    assert not kwargs
    assert len(args) == 1
    assert numpy.array_equal(
        args[0], numpy.array([int(b) for b in message_bits], dtype=numpy.uint8)
    )


@pytest.mark.parametrize(
    "signal",
    [
        b"\xff\xa8\xb3 \x90\x05\xef!\xff\xd4Y\x90G"
        b"\x02\xf7\x90\xff\xff\xff\xff\xff\xff\xff\xff\xff"
    ],
)
def test__parse_transmission_repeats_dont_match(signal):
    with pytest.raises(wireless_sensor.DecodeError, match=r"\brepeats do not match\b"):
        wireless_sensor.FT017TH._parse_transmission(
            numpy.frombuffer(signal, dtype=numpy.uint8)
        )


def test__receive_packet():
    with unittest.mock.patch("cc1101.CC1101"):
        sensor = wireless_sensor.FT017TH()
    with unittest.mock.patch("time.sleep") as sleep_mock:
        sensor._transceiver.get_marc_state.side_effect = (
            lambda: cc1101.MainRadioControlStateMachineState.RX
            if sum(a[0] for a, _ in sleep_mock.call_args_list) < 16
            else cc1101.MainRadioControlStateMachineState.IDLE
        )
        sensor._transceiver._get_received_packet.side_effect = (
            lambda: "fail"
            if sum(a[0] for a, _ in sleep_mock.call_args_list) < 16
            else "dummy"
        )
        packet = sensor._receive_packet()
    sensor._transceiver._enable_receive_mode.assert_called_once_with()  # pylint: disable=no-member; false positive
    assert sleep_mock.call_args_list == [
        unittest.mock.call(0.05),
        unittest.mock.call(8.0),
        unittest.mock.call(8.0),
    ]
    assert packet == "dummy"


def test__receive_measurement_unexpected_length():
    sensor = wireless_sensor.FT017TH()
    with unittest.mock.patch.object(
        sensor,
        "_receive_packet",
        return_value=cc1101._ReceivedPacket(
            data=b"\xff" * 17,
            rssi_index=0,
            checksum_valid=True,
            link_quality_indicator=0,
        ),
    ):
        with pytest.raises(wireless_sensor._UnexpectedPacketLengthError):
            sensor._receive_measurement()


def test_receive():
    with unittest.mock.patch("cc1101.CC1101"):
        sensor = wireless_sensor.FT017TH()
    measurement_iter = sensor.receive()
    packet = cc1101._ReceivedPacket(
        data=b"\0" * 21, rssi_index=0, checksum_valid=True, link_quality_indicator=0
    )
    with unittest.mock.patch.object(sensor, "_receive_packet") as receive_packet_mock:
        packet_queue = queue.Queue()
        packet_queue.put(None)
        packet_queue.put(None)
        packet_queue.put(packet)
        packet_queue.put(None)
        packet_queue.put(packet)
        receive_packet_mock.side_effect = packet_queue.get
        with unittest.mock.patch.object(
            sensor, "_parse_transmission", return_value="dummy"
        ) as parse_transmission_mock:
            assert next(measurement_iter) == "dummy"
        sensor._transceiver.__enter__.assert_called_once_with()  # pylint: disable=no-member; false positive
        assert receive_packet_mock.call_count == 3
        assert parse_transmission_mock.call_count == 1
        (
            parse_transmission_args,
            parse_transmission_kwargs,
        ) = parse_transmission_mock.call_args
        assert not parse_transmission_kwargs
        assert len(parse_transmission_args) == 1
        assert numpy.array_equal(
            parse_transmission_args[0],
            numpy.array([255, 168] + [0] * 21, dtype=numpy.uint8),
        )
        with unittest.mock.patch.object(
            sensor, "_parse_transmission", return_value="dummy2"
        ):
            assert next(measurement_iter) == "dummy2"
    # pylint: disable=no-member; false positive
    sensor._transceiver.unlock_spi_device.assert_not_called()


def test_receive_failed_to_decode(caplog):
    with unittest.mock.patch("cc1101.CC1101"):
        sensor = wireless_sensor.FT017TH()
    measurement_iter = sensor.receive()
    with unittest.mock.patch.object(
        sensor,
        "_receive_packet",
        return_value=cc1101._ReceivedPacket(
            data=b"\0" * 21, rssi_index=0, checksum_valid=True, link_quality_indicator=0
        ),
    ) as receive_packet_mock, unittest.mock.patch.object(
        sensor,
        "_parse_transmission",
        side_effect=[
            wireless_sensor.DecodeError("dummy error 0"),
            wireless_sensor.DecodeError("dummy error 1"),
            "dummy measurement",
        ],
    ) as parse_transmission_mock, caplog.at_level(
        logging.DEBUG
    ):
        assert next(measurement_iter) == "dummy measurement"
    assert receive_packet_mock.call_count == 3
    assert parse_transmission_mock.call_count == 3
    decode_error_log_records = [
        (r.message, r.exc_info[1])
        for r in caplog.records
        if r.name == "wireless_sensor"
        and r.funcName == "_receive_measurement"
        and r.exc_info
    ]
    assert len(decode_error_log_records) == 2
    for error_index in range(2):
        assert decode_error_log_records[error_index][0] == (
            "failed to decode _ReceivedPacket(RSSI -74dBm, 0x{}): ".format("00" * 21)
            + "dummy error {}".format(error_index)
        )
        assert isinstance(
            decode_error_log_records[error_index][1], wireless_sensor.DecodeError
        )


def test_receive_unexpected_packet_length(caplog):
    with unittest.mock.patch("cc1101.CC1101"):
        sensor = wireless_sensor.FT017TH()
    measurement = wireless_sensor.Measurement(
        decoding_timestamp=datetime.datetime.now(),
        temperature_degrees_celsius=21.0,
        relative_humidity=42.0,
    )
    with unittest.mock.patch.object(
        sensor,
        "_receive_measurement",
        side_effect=[
            wireless_sensor._UnexpectedPacketLengthError,
            wireless_sensor._UnexpectedPacketLengthError,
            measurement,
        ],
    ), caplog.at_level(logging.INFO):
        assert next(sensor.receive()) == measurement
    assert (
        # pylint: disable=no-member; false positive
        sensor._transceiver.__enter__.call_count
        == 1 + 2
    )
    assert (
        caplog.record_tuples
        == [
            (
                "wireless_sensor",
                logging.INFO,
                "unexpected packet length; "
                "reconfiguring as transceiver was potentially accessed by another process",
            )
        ]
        * 2
    )


def test_receive_locked(caplog):
    with unittest.mock.patch("cc1101.CC1101"):
        sensor = wireless_sensor.FT017TH()
    measurement = wireless_sensor.Measurement(
        decoding_timestamp=datetime.datetime.now(),
        temperature_degrees_celsius=21.0,
        relative_humidity=42.0,
    )
    with unittest.mock.patch.object(
        sensor._transceiver,
        "__enter__",
        side_effect=[
            BlockingIOError,
            BlockingIOError,
            BlockingIOError,
            sensor._transceiver,
        ],
    ) as enter_mock, unittest.mock.patch.object(
        sensor, "_receive_measurement", return_value=measurement
    ), unittest.mock.patch(
        "time.sleep"
    ) as sleep_mock, caplog.at_level(
        logging.INFO
    ):
        assert next(sensor.receive()) == measurement
    assert enter_mock.call_count == 4
    assert sleep_mock.call_args_list == [unittest.mock.call(s) for s in [2, 4, 8]]
    assert caplog.record_tuples == [
        (
            "wireless_sensor",
            logging.INFO,
            "SPI device locked, waiting {} seconds".format(seconds),
        )
        for seconds in [2, 4, 8]
    ]


def test_receive_no_reconfiguring(caplog):
    with unittest.mock.patch("cc1101.CC1101"):
        sensor = wireless_sensor.FT017TH()
    measurement = wireless_sensor.Measurement(
        decoding_timestamp=datetime.datetime.now(),
        temperature_degrees_celsius=21.0,
        relative_humidity=42.0,
    )
    with unittest.mock.patch.object(
        sensor, "_receive_measurement", return_value=measurement
    ), caplog.at_level(logging.INFO):
        measurement_iter = sensor.receive()
        for _ in range(3):
            assert next(measurement_iter) == measurement
    assert (
        # pylint: disable=no-member; false positive
        sensor._transceiver.__enter__.call_count
        == 1
    )
    assert not caplog.record_tuples


def test_receive_unlock_spi_device(caplog):
    with unittest.mock.patch("cc1101.CC1101") as transceiver_class_mock:
        sensor = wireless_sensor.FT017TH(unlock_spi_device=True)
    transceiver_class_mock.assert_called_once_with(lock_spi_device=True)
    measurement = wireless_sensor.Measurement(
        decoding_timestamp=datetime.datetime.now(),
        temperature_degrees_celsius=21.0,
        relative_humidity=42.0,
    )
    with unittest.mock.patch.object(
        sensor, "_receive_measurement", return_value=measurement
    ), caplog.at_level(logging.DEBUG):
        measurement_iter = sensor.receive()
        for _ in range(3):
            assert next(measurement_iter) == measurement
    transceiver_class_mock().unlock_spi_device.assert_called_once_with()
    assert len(caplog.records) == 2
    assert caplog.record_tuples[1] == (
        "wireless_sensor",
        logging.DEBUG,
        "unlocked SPI device",
    )
