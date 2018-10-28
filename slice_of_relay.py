#!/usr/bin/python
# -*- coding: utf-8 -*-
import wiringpi2
import sys
import argparse
a=24 # relay A 
b=25 # relay B
wiringpi2.wiringPiSetupGpio()
wiringpi2.pinMode(a, 1)
wiringpi2.pinMode(b, 1)
def relay(position='not_defined', pin=a):
  if (position != 'not_defined'):
    if (position == True or position == 'closed' or int(position) == 1):
        wiringpi2.digitalWrite(pin, 1)
    elif(position == False or position == 'open' or int(position) == 0):
        wiringpi2.digitalWrite(pin, 0)
    else:
      print('unknown position {}'.format(position))
  return wiringpi2.digitalRead(pin)

if __name__ == "__main__":
  parser = argparse.ArgumentParser(
    description=__doc__,
    formatter_class=argparse.RawDescriptionHelpFormatter)
  parser.add_argument('--relay', '-r', default='1', help='the relay number - 25=back hall, 24=main hall ')
  parser.add_argument('--position', '-p', default= 'not_defined', help='send interger 1 or "close" or boolean True to close the relay')

  flags=parser.parse_args(sys.argv[1:])
  print(relay(position=flags.position,pin=int(flags.relay)))
#  if len(sys.argv) == 2:
#    #print(sys.argv[1], type(sys.argv[1]))
#    print(relay(position=sys.argv[1]))
#  else:
#    print(relay())
