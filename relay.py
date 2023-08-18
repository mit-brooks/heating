#!/usr/bin/python
# -*- coding: utf-8 -*-
from gpiozero import DigitalOutputDevice  #
import gpiozero.pins.rpigpio
import sys
import argparse
a = 24  # relay A
b = 25  # relay B
s = 11  # SPI


def close(self):
    pass


gpiozero.pins.rpigpio.RPiGPIOPin.close = close


def relay(position='not_defined', pin=a):
    rly = DigitalOutputDevice(pin, initial_value=None, pin_factory=gpiozero.pins.rpigpio.RPiGPIOFactory())
    if position != 'not_defined':
        if position == 'closed' or int(position) == 1:
            rly.on()
            print("on")
        elif position == 'open' or int(position) == 0:
            rly.off()
            print("off")
        else:
            print('unknown position {}'.format(position))
    return rly.value


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('--relay', '-r', default='1', help='the relay number: \nSlice of pi: \n'
                                                           '   25=back hall, \n   24=main hall, \nBC Robitics 4 channel relay hat: \n'
                                                           '   4=Relay 1,\n   27=Relay 2,\n   22=relay3,\n   17=relay4')
    parser.add_argument('--position', '-p', default='not_defined',
                        help='send integer 1 or "close" or boolean True to close the relay')

    flags = parser.parse_args(sys.argv[1:])
    print(relay(position=flags.position, pin=int(flags.relay)))
#  if len(sys.argv) == 2:
#    #print(sys.argv[1], type(sys.argv[1]))
#    print(relay(position=sys.argv[1]))
#  else:
#    print(relay())
