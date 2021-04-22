# wireless-sensor 🌡

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![CI Pipeline Status](https://github.com/fphammerle/wireless-sensor/workflows/tests/badge.svg)](https://github.com/fphammerle/wireless-sensor/actions)
[![Coverage Status](https://coveralls.io/repos/github/fphammerle/wireless-sensor/badge.svg?branch=master)](https://coveralls.io/github/fphammerle/wireless-sensor?branch=master)
[![Last Release](https://img.shields.io/pypi/v/wireless-sensor.svg)](https://pypi.org/project/wireless-sensor/#history)
[![Compatible Python Versions](https://img.shields.io/pypi/pyversions/wireless-sensor.svg)](https://pypi.org/project/wireless-sensor/)
[![DOI](https://zenodo.org/badge/319298583.svg)](https://zenodo.org/badge/latestdoi/319298583)

Command-line tool & python library to receive & decode signals of FT017TH wireless thermo/hygrometers

## Requirements

* [FT017TH](https://github.com/fphammerle/FT017TH-wireless-thermometer-hygrometer-signal#product-details) sensor
* [CC1101 transceiver](https://www.ti.com/product/CC1101)
* Linux machine with CC1101 connected to SPI port & `GDO0` connected to some GPIO pin
  ([wiring instructions](https://github.com/fphammerle/python-cc1101#wiring-raspberry-pi)
  for raspberry pi)

## Setup

```sh
$ pip3 install --user --upgrade wireless-sensor
```

## Usage

### Command-line

```sh
$ wireless-sensor-receive
2020-12-07T10:40:16+0100 23.9°C 46.9%
2020-12-07T10:41:04+0100 23.9°C 46.9%
2020-12-07T10:42:01+0100 23.8°C 47.0%
```

### Python Library

```python
import wireless_sensor

sensor = wireless_sensor.FT017TH(gdo0_gpio_line_name=b'GPIO24')
for measurement in sensor.receive(timeout_seconds=600):
    if not measurement:
        print("invalid packet or timeout")
        continue
    print(
        measurement.decoding_timestamp,
        measurement.temperature_degrees_celsius,
        measurement.relative_humidity,
    )
```
