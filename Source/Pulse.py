import BotpySE as bp
import chatexchange as ce
from HalflifeListener import *
from DeepSmokeListener import *
from CommandUpdate import *
from Notifications import *

class Pulse:
    def __init__ (self, nick, email, password, rooms):
        client = ce.Client("stackexchange.com", email, password)

        commands = bp.all_commands
        commands.extend([
            CommandUpdate,
            CommandNotifications,
            CommandNotify,
            CommandUnnotify
            ])

        bot = bp.Bot(nick, client, commands, rooms)

        notifications = Notifications(rooms)
        bot.chatcommunicate.command_manager.notifications = notifications

        bot.start_bot()

        bot.add_privilege_type(1, "owner")

        bot.add_essential_background_tasks()

        roomlist = bot.rooms
        halflife = HalflifeListener(roomlist[0], roomlist, notifications)
        #deep_smoke = DeepSmokeListener(roomlist[0], roomlist, notifications)

        halflife.start()
        #deep_smoke.start()

        while bot.is_alive:
            pass

        halflife.stop()
        #deep_smoke.stop()
