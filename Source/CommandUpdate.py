#
# CommandUpdate.py
# Botpy
#
# Created by Ashish Ahuja on 5th October 2017.
# This file is licensed under the MIT License.
#

from BotpySE import Command, Utilities
import subprocess

class CommandUpdate(Command):
    @staticmethod
    def usage():
        return ["update", "pull"]

    def run(self):
        print("UPDATE")
        subprocess.call(['git', 'pull', 'origin', 'master'])
        self.reply("Updating...")
        Utilities.should_reboot = True
