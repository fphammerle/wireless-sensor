import datetime
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
    parse_message_mock.assert_called_once()
    args, kwargs = parse_message_mock.call_args
    assert not kwargs
    assert len(args) == 1
    assert numpy.array_equal(
        args[0], numpy.array([int(b) for b in message_bits], dtype=numpy.uint8)
    )


def test__receive_packet():
    with unittest.mock.patch("cc1101.CC1101"):
        sensor = wireless_sensor.FT017TH()
    with unittest.mock.patch("time.sleep") as sleep_mock:
        sensor.transceiver.get_marc_state.side_effect = (
            lambda: cc1101.MainRadioControlStateMachineState.RX
            if sum(a[0] for a, _ in sleep_mock.call_args_list) < 16
            else cc1101.MainRadioControlStateMachineState.IDLE
        )
        sensor.transceiver._get_received_packet.side_effect = (
            lambda: "fail"
            if sum(a[0] for a, _ in sleep_mock.call_args_list) < 16
            else "dummy"
        )
        packet = sensor._receive_packet()
    sensor.transceiver._enable_receive_mode.assert_called_once_with()  # pylint: disable=no-member; false positive
    assert sleep_mock.call_args_list == [
        unittest.mock.call(0.05),
        unittest.mock.call(8.0),
        unittest.mock.call(8.0),
    ]
    assert packet == "dummy"
