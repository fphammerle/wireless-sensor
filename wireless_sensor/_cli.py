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

import argparse
import logging

import wireless_sensor


def _receive():
    argparser = argparse.ArgumentParser(
        description="Receive & decode signals of FT017TH thermo/hygrometers"
    )
    argparser.add_argument(
        "--gdo0-gpio-line-name",
        type=str,
        # GPIO24 recommended at
        # https://github.com/fphammerle/python-cc1101/tree/v2.7.3#wiring-raspberry-pi
        default="GPIO24",
        help="Name of GPIO pin that CC1101's GDO0 pin is connected to."
        " Run command `gpioinfo` to get a list of all available GPIO lines."
        " Default: %(default)s",
    )
    argparser.add_argument(
        "--unlock-spi-device",
        action="store_true",
        help="Release flock from SPI device file after configuring the transceiver."
        " Useful if another process (infrequently) accesses the transceiver simultaneously.",
    )
    argparser.add_argument("--debug", action="store_true")
    args = argparser.parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="%(asctime)s:%(levelname)s:%(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z",
    )
    logging.getLogger("cc1101").setLevel(logging.INFO)
    sensor = wireless_sensor.FT017TH(
        gdo0_gpio_line_name=args.gdo0_gpio_line_name.encode(),
        unlock_spi_device=args.unlock_spi_device,
    )
    for measurement in filter(None, sensor.receive(timeout_seconds=60 * 60 * 24)):
        print(
            "{:%Y-%m-%dT%H:%M:%S%z}\t{:.01f}°C\t{:.01f}%".format(
                measurement.decoding_timestamp,
                measurement.temperature_degrees_celsius,
                measurement.relative_humidity * 100,
            )
        )
