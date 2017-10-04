#
# startup.py
# PulseMonitor
#
# Created by Ashish Ahuja on 23rd September 2017.
# This file is licensed under the MIT License.
#

import BotpySE as bp
import chatexchange as ce
import os
import getpass
from HalflifeListener import *
from DeepSmokeListener import *

if 'PulseEmail' in os.environ:
    email = os.environ['PulseEmail']
else:
    email = input("Email: ")

if 'PulsePass' in os.environ:
    password = os.environ['PulsePass']
else:
    password = getpass.getpass("Password: ")

client = ce.Client("stackexchange.com", email, password)

commands = bp.all_commands

bot = bp.Bot("pulsemonitor", client, commands, [65945, 64277])

bot.start_bot()

bot.add_privilege_type(1, "owner")

bot.add_essential_background_tasks()

rooms = list()

for each_room in bot.rooms:
    rooms.append(each_room.room)

halflife = HalflifeListener(bot.rooms[0].room, rooms)
deep_smoke = DeepSmokeListener(bot.rooms[0].room, rooms)

#halflife.start()
deep_smoke.start()

while bot.is_alive:
    pass

#halflife.stop()
deep_smoke.stop()
