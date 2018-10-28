""" test ebe_relay.py"""

import mock
import ebe_relay
import unittest
from random import randint

import os, pty, serial


class EbeRelayTest(unittest.TestCase):
    """tests for ebe relay
    """

    master, slave = pty.openpty()
    s_name = os.ttyname(slave)
    d_pos = 0
    def dummy_relay():
        while true:
            cmd = os.read(self.master,1000)        
            if cmd == '[':
                return self.d_pos
            if cmd == 'e':
                self.d_pos |= 1
            if cmd == 'f' :
                self.d_pos |= 2
            if cmd == 'o':
                self.d_pos &= 2
            if cmd == 'p':
                self.d_pos &= 1
            
    def test_relay_read(self):
        r=ebe_relay.relay(self.s_name)
        assert(r == 0)

if __name__ == "__main__":
    unittest.main()
