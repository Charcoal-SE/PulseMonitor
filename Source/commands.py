import BotpySE as bp


class CommandPrivilegeUser(bp.CommandPrivilegeUser):
    def privileges(self):
        return 1

class CommandUnprivilegeUser(bp.CommandUnprivilegeUser):
    def privileges(self):
        return 1

class CommandStop(bp.CommandStop):
    def privileges(self):
        return 1

class CommandReboot(bp.CommandReboot):
    def privileges(self):
        return 1

default_commands = [bp.CommandAlive, bp.CommandListRunningCommands, CommandPrivilegeUser, CommandStop, CommandUnprivilegeUser, bp.CommandAmiprivileged, bp.CommandListPrivilegedUsers, CommandReboot]
