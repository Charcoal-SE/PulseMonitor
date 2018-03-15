import os
import getpass

from Pulse import *

if 'PulseEmail' in os.environ:
    email = os.environ['PulseEmail']
else:
    email = input("Email: ")

if 'PulsePass' in os.environ:
    password = os.environ['PulsePass']
else:
    password = getpass.getpass("Password: ")

Pulse("pulsemonitor", email, password, rooms=[65945])
