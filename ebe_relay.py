#!/usr/bin/python
# -*- coding: utf-8 -*-
"""control a relay on the end of a serial connection
In this case, it is a serial usb connection with 2 Relay at the end.
To read the relay value, send a '[' then read the returned value.
So long as something is returned, bit one is the status of relay one, bit 2 is the status of relay 2.
binary '1' means the relay is closed.

The following are teh codes to control the relays
char d (decimal 100) turns both relays on (close circuit)
char e (decimal 101) turns relay 1 on
char f (decimal 102) turns relay 2 on
char n (decimal 110) turns both relays off (open circuit)
char o (decimal 111) turns relay 1 off
char p (decimal 112) turns relay 2 off
"""


import argparse
import sys
import serial

import binascii

# back hal realy is number 1, main hall number 2
RELAY = 1

def rd(pin, ser):
  while True :
    ser.write('[')
    r=ser.read()
    if r != '' :
      break
  return (int(binascii.hexlify(r)) & pin)>>(pin-1)


def relay(dev='/dev/ttyACM0',
          position='not_defined',
          pin=RELAY):

  # relay choises
  if (pin == 1):
    on  = 'e'
    off = 'o'
  elif(pin == 2):
    on  = 'f'
    off = 'p'
    
  # open serial connection
  ser = serial.Serial(dev, timeout = 4)
  # dummy read
  rd(pin, ser)

  #
  if (position != 'not_defined'):
    if (position == True or position == 'closed' or int(position) == 1):
      ser.write(on)
    elif(position == False or position == 'open' or int(position) == 0):
      ser.write(off)
    else:
      print('unknown position {}'.format(position))
  return rd(pin, ser)

if __name__ == "__main__":

  parser = argparse.ArgumentParser(
    description=__doc__,
    formatter_class=argparse.RawDescriptionHelpFormatter)
  parser.add_argument('--relay', '-r', default='1', help='the relay number - 1=back hall, 2=main hall ')
  parser.add_argument('--position', '-p', default= 'not_defined', help='send interger 1 or "close" or boolean True to close the relay')

  flags=parser.parse_args(sys.argv[1:])
  print(relay(position=flags.position,pin=int(flags.relay)))
