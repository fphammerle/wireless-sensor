import datetime
import enum
import json
import logging
import math
import pathlib
import struct
import time
import typing

import cc1101
import manchester_code
import numpy

_MESSAGE_LENGTH_BITS = 65
_MESSAGE_REPEATS = 3

def _parse_transmission(signal: 'numpy.ndarray(dtype=numpy.uint8)') -> None:
    bits = numpy.unpackbits(signal)[:_MESSAGE_LENGTH_BITS * _MESSAGE_REPEATS] #bitorder='big'
    repeats_bits = numpy.split(bits, _MESSAGE_REPEATS)
    # cc1101 might have skipped the first repeat
    if numpy.array_equal(repeats_bits[0], repeats_bits[1]) or numpy.array_equal(repeats_bits[0], repeats_bits[2]):
        _parse_message(repeats_bits[0])
    else:
        logging.debug("repeats do not match, ignoring transmission")

def _parse_message(bits) -> None:
    assert bits.shape == (_MESSAGE_LENGTH_BITS,), bits.shape
    if (bits[:8] != 1).any():
        logging.info("invalid prefix in message: %s", bits)
        return
    temperature_index, = struct.unpack(
        ">H", numpy.packbits(bits[32:44]) # , bitorder="big")
    )
    # advertised range: [-40°C, +60°C]
    # intercept: -40°C = -40°F
    # slope estimated with statsmodels.regression.linear_model.OLS
    # 12 bits have sufficient range: 2**12 * slope / 2**4 - 40 = 73.76
    temperature_celsius = temperature_index / 576.077364 - 40
    # advertised range: [10%, 99%]
    # intercept: 0%
    # slope estimated with statsmodels.regression.linear_model.OLS
    # 12 bits have sufficient range: 2**12 * slope / 2**4 + 0 = 1.27
    relative_humidity_index, = struct.unpack(
        ">H", numpy.packbits(bits[44:56]) #, bitorder="big")
    )
    relative_humidity = relative_humidity_index / 51451.432435
    logging.info(
        "%s %.02f°C %.01f%% %s",
        numpy.packbits(bits[8:32]), # address & battery?
        temperature_celsius,
        relative_humidity*100,
        bits[56:], # checksum?
    )

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s:%(levelname)s:%(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S%z",
)
logging.getLogger("cc1101").setLevel(logging.INFO)

with cc1101.CC1101() as transceiver:
    transceiver.set_base_frequency_hertz(433.945e6)
    transceiver.set_symbol_rate_baud(2048)
    transceiver.set_sync_mode(cc1101.SyncMode.TRANSMIT_16_MATCH_15_BITS, _carrier_sense_threshold_enabled=True)
    sync_word = bytes([255, 168])
    transceiver.set_sync_word(sync_word)
    transceiver.disable_checksum()
    transceiver.enable_manchester_code()
    transceiver.set_packet_length_mode(cc1101.PacketLengthMode.FIXED)
    transceiver.set_packet_length_bytes(math.ceil(_MESSAGE_LENGTH_BITS * _MESSAGE_REPEATS / 8) - len(sync_word))
    transceiver._set_filter_bandwidth(mantissa=3, exponent=3)
    #transceiver._write_burst(start_register=cc1101.ConfigurationRegisterAddress.PKTCTRL1, values=[0b00100100])
    #mdmcfg2 = transceiver._read_single_byte(cc1101.ConfigurationRegisterAddress.MDMCFG2)
    #mdmcfg2 |= 0b00000100
    #transceiver._write_burst(cc1101.ConfigurationRegisterAddress.MDMCFG2, [mdmcfg2])
    print(transceiver)
    print('filter bandwidth: {:.0f} kHz'.format(transceiver._get_filter_bandwidth_hertz() / 1000))
    print("flushing...")
    transceiver._command_strobe(cc1101.StrobeAddress.SFRX)
    time.sleep(0.1)
    while True:
         transceiver._enable_receive_mode()
         time.sleep(0.05)
         while transceiver.get_marc_state() == cc1101.MainRadioControlStateMachineState.RX:
             time.sleep(8.0)
         packet = transceiver._get_received_packet()
         if packet:
             logging.debug("%s", packet)
             _parse_transmission(numpy.frombuffer(sync_word + packet.data, dtype=numpy.uint8))
