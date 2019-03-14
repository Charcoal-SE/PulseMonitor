import os
import subprocess
import logging

import BotpySE as bp
import chatexchange as ce

from HalflifeListener import *
from DeepSmokeListener import *
from CommandUpdate import *
from Notifications import *
from Tagging import *
from commands import *


class Pulse:
    def __init__ (self, nick, email, password, rooms):
        commands = default_commands
        commands.extend([
            CommandUpdate,
            CommandNotifications,
            CommandNotify,
            CommandUnnotify,
            CommandListTags,
            CommandAddTag,
            CommandRemoveTag
            ])

        version_hash = self._get_current_hash()

        self._bot_header = r'\[[PulseMonitor]' \
            '(https://github.com/Charcoal-SE/PulseMonitor) ' + \
                version_hash + r'\]'

        bot = bp.Bot(nick, commands, rooms, [], "stackexchange.com", email, password)
        bot.add_alias("Halflife")

        try:
            with open(bot._storage_prefix + 'redunda_key.txt', 'r') as file_handle:
                key = file_handle.readlines()[0].rstrip('\n')
            bot.set_redunda_key(key)

            bot.add_file_to_sync({"name": bot._storage_prefix + 'tags.json',
                "ispickle": False, "at_home": False})
            bot.add_file_to_sync({"name": bot._storage_prefix + 'notifications.json',
                "ispickle": False, "at_home": False})
            bot.redunda_init(bot_version=version_hash)
            bot.set_redunda_default_callbacks()
            bot.set_redunda_status(True)

        except IOError as ioerr:
            logging.error(str(ioerr))
            logging.warn("Bot is not integrated with Redunda.")

        bot.set_startup_message(self._bot_header +
            " started on " + bot._location + ".")
        bot.set_standby_message(self._bot_header +
            " running on " + bot._location + " shifting to standby.")
        bot.set_failover_message(self._bot_header +
            " running on " + bot._location + " received failover.")

        notifications = Notifications(
            rooms, bot._storage_prefix + 'notifications.json')
        tags = TagManager(bot._storage_prefix + 'tags.json')
        bot._command_manager.notifications = notifications
        bot._command_manager.tags = tags

        bot.start()
        bot.add_privilege_type(1, "owner")
        bot.set_room_owner_privs_max()

        roomlist = bot._rooms
        halflife = HalflifeListener(
            roomlist[0], roomlist, notifications, bot._command_manager.tags)
        #deep_smoke = DeepSmokeListener(roomlist[0], roomlist, notifications)

        halflife.start()
        #deep_smoke.start()

        while bot.is_alive:
            pass

        halflife.stop()
        #deep_smoke.stop()

    def _get_current_hash(self):
        return subprocess.run(['git', 'log', '-n', '1', '--pretty=format:"%H"'],
            stdout=subprocess.PIPE).stdout.decode('utf-8')[1:7]
