import datetime
import logging
import unittest.mock

import pytest

import wireless_sensor
import wireless_sensor._cli

# pylint: disable=protected-access


@pytest.mark.parametrize(
    ("argv", "root_log_level"), [([""], logging.INFO), (["", "--debug"], logging.DEBUG)]
)
def test__receive(capsys, argv, root_log_level):
    with unittest.mock.patch("wireless_sensor.FT017TH") as sensor_class_mock:
        sensor_class_mock().receive.return_value = [
            wireless_sensor._Measurement(
                decoding_timestamp=datetime.datetime(2020, 12, 7, 10, 0, 0),
                temperature_degrees_celsius=24.1234,
                relative_humidity=0.51234,
            ),
            wireless_sensor._Measurement(
                decoding_timestamp=datetime.datetime(2020, 12, 7, 10, 0, 50),
                temperature_degrees_celsius=22.42,
                relative_humidity=0.55123,
            ),
            wireless_sensor._Measurement(
                decoding_timestamp=datetime.datetime(2020, 12, 7, 10, 1, 41),
                temperature_degrees_celsius=21.1234,
                relative_humidity=0.61234,
            ),
        ]
        with unittest.mock.patch("sys.argv", argv), unittest.mock.patch(
            "logging.basicConfig"
        ) as logging_basic_config_mock:
            wireless_sensor._cli._receive()
    logging_basic_config_mock.assert_called_once()
    assert logging_basic_config_mock.call_args[1]["level"] == root_log_level
    assert logging.getLogger("cc1101").getEffectiveLevel() == logging.INFO
    out, err = capsys.readouterr()
    assert not err
    assert out == (
        "2020-12-07T10:00:00\t24.1°C\t51.2%\n"
        "2020-12-07T10:00:50\t22.4°C\t55.1%\n"
        "2020-12-07T10:01:41\t21.1°C\t61.2%\n"
    )
