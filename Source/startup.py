import os
import getpass
import logging

from Pulse import *


if 'PulseEmail' in os.environ:
    email = os.environ['PulseEmail']
else:
    email = input("Email: ")

if 'PulsePass' in os.environ:
    password = os.environ['PulsePass']
else:
    password = getpass.getpass("Password: ")

logging.basicConfig(format='%(asctime)s:%(module)s:%(message)s', level=logging.info)
Pulse("PulseMonitor", email, password, rooms=[65945])
