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

if 'PulseEmail' in os.environ:
    email = os.environ['PulseEmail']
else:
    email = input("Email: ")

if 'PulsePass' in os.environ:
    password = os.environ['PulsePass']
else:
    password = getpass.getpass("Password: ")

client = ce.Client("stackexchange.com", email, password)

commands = [bp.CommandAlive, bp.CommandStop, bp.CommandListRunningCommands]

bot = bp.Bot("pulsemonitor", client, commands, [65945])

bot.start_bot()

bot.add_privilege_type(1, "owner")

bot.add_essential_background_tasks()

rooms = list()

for each_room in bot.rooms:
    rooms.append(each_room.room)

halflife = HalflifeListener(bot.rooms[0].room, rooms)

halflife.start()
