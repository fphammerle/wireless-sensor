# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Fixed
- `ValueError: astimezone() cannot be applied to a naive datetime` on python3.5

## [0.1.0] - 2020-02-06
### Added
- method `wireless_sensor.FT017TH.receive` continuously yielding
  temperature & humidity measurements received from FT017TH sensor
- script `wireless-sensor-receive`

[Unreleased]: https://github.com/fphammerle/wireless-sensor/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/fphammerle/wireless-sensor/releases/tag/v0.1.0
