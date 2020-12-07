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
