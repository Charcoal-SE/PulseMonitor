import json
import logging
import re
from copy import deepcopy
from functools import wraps
from textwrap import indent
from threading import Lock

from BotpySE import Command
import tabulate

from regex import normalize


logger = logging.getLogger(__name__)


def _at_notification(username, _sub=re.compile(r"[^\w'.-]*").sub):
    """Produce the @DisplayName notification normazilation form"""
    return "@" + _sub("", username)


def _as_inline_code(text):
    """Apply inline code markdown to text

    Wrap text in backticks, escaping any embedded backticks first.

    E.g:

        >>> print(_as_inline_code("foo [`']* bar"))
        `foo [\\`']* bar`

    """
    escaped = text.replace("`", r"\`")
    return f"`{escaped}`"


class Notifications:
    def __init__(self, rooms, filename="./notifications.json"):
        self.filename = filename
        self._lock = Lock()
        try:
            with open(filename, "r", encoding="utf8") as notifications_file:
                self.notifications, self.users = json.load(notifications_file)
        except FileNotFoundError:
            self.notifications = {}
            self.users = {}

        for room in rooms:
            room = str(room)
            if room not in self.notifications:
                self.notifications[room] = {}

    def _save(self, filename=None):
        """Write out the notifications data.

        Not thread-safe, when called from a thread caller is
        expected to obtain the lock.

        """
        if filename is None:  # pragma: no cover
            filename = self.filename
        with open(filename, "w", encoding="utf8") as notifications_file:
            json.dump([self.notifications, self.users], notifications_file)

    def add(self, room, regex, user, user_name):
        """Add the regex pattern to the room notifications for the given user

        Returns True when the pattern wasn't yet registered for this user,
        False otherwise.

        """
        room, user = str(room), str(user)
        with self._lock:
            if room not in self.notifications:
                return False

            regexes_for_room = self.notifications[room]
            # make sure we have a dictionary to for users to notify when their
            # regex matches
            users_for_regex = regexes_for_room.setdefault(regex, [])

            # only add a user if not already listed
            if user in users_for_regex:
                return False

            users_for_regex.append(user)
            self.users[user] = user_name
            self._save()
            return True

    def list(self, room=None):
        """Generate all notification entries

        Entries are yielded as (room_id, regex, user_id, username) tuples

        If room is not None, then the list is filtered by that room.

        """
        with self._lock:
            # minimise locking time by creating a copy to iterate over
            notifications = deepcopy(self.notifications)

        for room_id, regexes in notifications.items():
            if not (room is None or str(room) == room_id):
                continue
            for regex, users in regexes.items():
                for user_id in users:
                    yield room_id, regex, user_id, self.users[user_id]

    def _remove(self, room, regex, user):
        """Helper function for remove_matching to remove matched patterns

        Not thread-safe, caller must hold lock when in a thread.

        """
        regexes_for_room = self.notifications[room]
        users_for_regex = regexes_for_room[regex]

        # users may have been added multiple times in the past, so make sure
        # we remove them all.
        while user in users_for_regex:
            users_for_regex.remove(user)

        if not users_for_regex:
            # remove regex from room when there are no users left to notify
            del regexes_for_room[regex]

    def remove_matching(self, room, expr, user):
        """Remove matching patterns

        expr is treated both as the regex itself, and as regex pattern that
        is used to search the stored patterns.

        Returns a list of removed patterns.

        """
        room, user = str(room), str(user)
        as_pattern = re.compile(expr, re.I)

        to_remove = []

        with self._lock:
            regexes_for_room = self.notifications.get(room, {})
            for regex, users_for_regex in regexes_for_room.items():
                # check for exact match or pattern match
                if regex == expr or as_pattern.search(regex):
                    if user in users_for_regex:
                        to_remove.append(regex)

            # remove regexes after matching, to avoid mutating-while-iterating
            for regex in to_remove:
                self._remove(room, regex, user)

            if to_remove:
                self._save()

        return to_remove

    def filter_post(self, room, post):
        """Check a post against the patterns registered for a room"""
        room = str(room)
        to_notify = set()

        with self._lock:
            # minimise locking time by creating pre-processed copies
            regexes_for_room = self.notifications.get(room, {})
            regexes = {p: set(u) for p, u in regexes_for_room.items()}
            at_names = {u: _at_notification(n) for u, n in self.users.items()}

        for regex, users_for_regex in regexes.items():
            if re.search(regex, post):
                to_notify.update(users_for_regex)

        if not to_notify:
            return post

        notifications = " ".join([at_names[user] for user in to_notify])
        return f"{post} {notifications}"


def _handle_exceptions(f):
    """Handle any exceptions in a Command.run method, and log and report"""

    @wraps(f)
    def wrapper(self, *args, **kwargs):
        try:
            return f(self, *args, **kwargs)
        except Exception as err:
            logger.exception(
                f"{type(self).__name__}.{f.__name__}(*{args!r}, **{kwargs!r}) failed"
            )
            content = self.message.content
            self.reply(f"Oops, the {content} command encountered a problem: {err!r}")

    wrapper._handle_exceptions = True
    return wrapper


class NotificationsCommandBase(Command):
    """Base class for notifications commands

    Provides a notifications attribute for access to the storage instance
    and a raw_arg property for un-processed argument access.

    """

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        # auto-decorate the run method in an exception handler.
        if not getattr(cls.run, "_handle_exceptions", False):  # pragma: no cover
            cls.run = _handle_exceptions(cls.run)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.notifications = self.command_manager.notifications

    @property
    def raw_arg(self):
        """Message argument as one string, with spaces and case preserved"""
        command = self.usage()[self.usage_index].partition(" ")[0]
        # TODO: would self.message.text_content be better here?
        message = self.message.content
        # remove command
        return message.partition(command)[2].strip()


class CommandNotifications(NotificationsCommandBase):
    @staticmethod
    def usage():
        return ["notifications"]

    def run(self):
        room = str(self.message.room.id)
        logger.info(f"NOTIFICATIONS by {self.message.user.id} in {room}")
        entries = [[user, pat] for _, pat, _, user in self.notifications.list(room)]
        table = tabulate.tabulate(entries, headers=["User", "Regex"], tablefmt="orgtbl")
        self.post(indent(table, "    "), False)


class CommandNotify(NotificationsCommandBase):
    @staticmethod
    def usage():
        return ["notify * ..."]

    def run(self):
        room = self.message.room.id
        user_id = self.message.user.id
        user_name = self.message.user.name
        # Take pattern from original message to preserve case and spacing
        # then normalize (remove residual <code>...</code> HTML formatting)
        pattern = normalize(self.raw_arg)
        markedup = _as_inline_code(pattern)
        logger.info(f"NOTIFY {user_id} in {room} for {pattern}")
        try:
            re.compile(pattern)
        except re.error as err:
            self.reply(f"Could not add notification {markedup}: {err}")
            return

        if self.notifications.add(room, pattern, user_id, user_name):
            self.reply(f"Added notification for {user_name} for {markedup}")
        else:
            self.reply(f"Pattern {markedup} already registered for {user_name}")


class CommandUnnotify(NotificationsCommandBase):
    @staticmethod
    def usage():
        return ["unnotify * ..."]

    def run(self):
        room = self.message.room.id
        user_id = self.message.user.id
        user_name = self.message.user.name
        # Take pattern from original message to preserve case and spacing
        # then normalize (remove residual <code>...</code> HTML formatting)
        pattern = normalize(self.raw_arg)
        markedup = _as_inline_code(pattern)
        logger.info(f"UNNOTIFY {pattern} for {user_id} in {room}")
        try:
            re.compile(pattern)
        except re.error as err:
            self.reply(
                f"Could not remove notification {markedup}: {err}"
            )
            return

        removed = self.notifications.remove_matching(room, pattern, user_id)
        if removed:
            joined = ", ".join([_as_inline_code(pat) for pat in removed])
            self.reply(f"Removed notifications: {joined}")
        else:
            self.reply(f"No matches on {markedup} for {user_name}")
