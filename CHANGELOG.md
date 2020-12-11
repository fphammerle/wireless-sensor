# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Changed
- lock SPI device file
- attribute `FT017TH.transceiver` is now private

### Added
- added option `FT017TH(unlock_spi_device=True)` to release `flock`
  on the SPI device file after configuring the transceiver

### Fixed
- reconfigure receiver after receiving a packet with unexpected length
  (receiver possibly accessed by other process)

## [0.2.0] - 2020-12-07
### Added
- `Measurement` type is now public

## [0.1.1] - 2020-12-07
### Fixed
- `ValueError: astimezone() cannot be applied to a naive datetime` on python3.5

## [0.1.0] - 2020-02-07
### Added
- method `wireless_sensor.FT017TH.receive` continuously yielding
  temperature & humidity measurements received from FT017TH sensor
- script `wireless-sensor-receive`

[Unreleased]: https://github.com/fphammerle/wireless-sensor/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/fphammerle/wireless-sensor/compare/v0.1.1...v0.2.0
[0.1.1]: https://github.com/fphammerle/wireless-sensor/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/fphammerle/wireless-sensor/releases/tag/v0.1.0
