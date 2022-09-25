#!/usr/bin/python
# -*- coding: utf-8 -*-
from gpiozero import LED  # Relay can look like an LED ;-)
import sys
import argparse
a = 24  # relay A
b = 25  # relay B
s = 11  # SPI


def relay(position='not_defined', pin=a):
    rly = LED(pin, initial_value=None)
    if position != 'not_defined':
        if position == 'closed' or int(position) == 1 or position:
            rly.on()
            print("on")
        elif position == 'open' or int(position) == 0 or not position:
            rly.off()
            print("off")
        else:
            print('unknown position {}'.format(position))
    val = rly.value
    print(f"relay value{val}")
    rly.close()
    return val


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--relay', '-r', default='1', help='the relay number - 25=back hall, 24=main hall ')
    parser.add_argument('--position', '-p', default='not_defined',
                        help='send integer 1 or "close" or boolean True to close the relay')

    flags=parser.parse_args(sys.argv[1:])
    print(relay(position=flags.position, pin=int(flags.relay)))
#  if len(sys.argv) == 2:
#    #print(sys.argv[1], type(sys.argv[1]))
#    print(relay(position=sys.argv[1]))
#  else:
#    print(relay())
