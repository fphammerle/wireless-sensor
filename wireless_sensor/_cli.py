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
    argparser.add_argument("--debug", action="store_true")
    args = argparser.parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="%(asctime)s:%(levelname)s:%(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z",
    )
    logging.getLogger("cc1101").setLevel(logging.INFO)
    for measurement in wireless_sensor.FT017TH().receive():
        print(
            "{:%Y-%m-%dT%H:%M:%S%z}\t{:.01f}°C\t{:.01f}%".format(
                measurement.decoding_timestamp,
                measurement.temperature_degrees_celsius,
                measurement.relative_humidity * 100,
            )
        )
