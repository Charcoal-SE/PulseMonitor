import json
import logging
import time
import threading
import traceback
from queue import SimpleQueue
from types import SimpleNamespace
from unittest import mock

import pytest


class _NotificationsTestsBase:
    @pytest.fixture(autouse=True)
    def setup_notifications(self, tmp_path, caplog):
        """Fixtures for notifications tests

        - Provide Notifications instance self.notifications with temporary file
          location (available as self.filepath)

        - Capture Notifications.py logging in self.logs

        """
        self.filepath = tmp_path / "notifications.json"
        self.create_notifications()

        self.logs = caplog
        self.logs.set_level(logging.INFO, logger="Notifications")

    def create_notifications(self):
        from Notifications import Notifications

        self.notifications = Notifications([17, 42], self.filepath)

    @property
    def saved_notifications(self):
        try:
            return json.loads(self.filepath.read_text())[0]
        except FileNotFoundError:
            return None

    @property
    def saved_users(self):
        try:
            return json.loads(self.filepath.read_text())[1]
        except FileNotFoundError:
            return None


class TestNotifications(_NotificationsTestsBase):
    def test_list_empty(self):
        assert list(self.notifications.list()) == []
        assert list(self.notifications.list(42)) == []
        assert list(self.notifications.list(-1)) == []

    def test_list_all(self):
        notifications = self.notifications
        notifications.add(17, r"foo .* bar", 13, "Graham Chapman")
        notifications.add(42, r"Monty (Python|Hall)", 23, "Terry Gilliam")

        assert sorted(notifications.list()) == [
            ("17", "foo .* bar", "13", "Graham Chapman"),
            ("42", "Monty (Python|Hall)", "23", "Terry Gilliam"),
        ]

    def test_list_filtered(self):
        notifications = self.notifications
        notifications.add(17, r"foo .* bar", 13, "Graham Chapman")
        notifications.add(42, r"Monty (Python|Hall)", 23, "Terry Gilliam")

        assert list(notifications.list(17)) == [
            ("17", "foo .* bar", "13", "Graham Chapman")
        ]
        assert list(notifications.list(42)) == [
            ("42", "Monty (Python|Hall)", "23", "Terry Gilliam"),
        ]
        assert list(notifications.list(9999)) == []

    def test_add(self):
        notifications = self.notifications
        notifications.add(17, r"foo .* bar", 13, "Graham Chapman")
        notifications.add(42, r"Monty (Python|Hall)", 23, "Terry Gilliam")

        assert self.saved_notifications == {
            "17": {"foo .* bar": ["13"]},
            "42": {"Monty (Python|Hall)": ["23"]},
        }
        assert self.saved_users == {"13": "Graham Chapman", "23": "Terry Gilliam"}

    def test_add_nonexistent(self):
        notifications = self.notifications
        notifications.add(9999, r"foo .* bar", 13, "Graham Chapman")

        # nothing changed, nothing saved
        assert self.saved_notifications is None

    def test_add_shared_pattern(self):
        notifications = self.notifications
        notifications.add(17, r"foo .* bar", 13, "Graham Chapman")
        notifications.add(17, r"foo .* bar", 23, "Terry Gilliam")

        assert self.saved_notifications == {
            "17": {"foo .* bar": ["13", "23"]},
            "42": {},
        }
        assert self.saved_users == {"13": "Graham Chapman", "23": "Terry Gilliam"}

    def test_add_repeated(self):
        notifications = self.notifications
        assert notifications.add(17, r"foo .* bar", 13, "Graham Chapman")
        assert not notifications.add(17, r"foo .* bar", 13, "Graham Chapman")

        assert self.saved_notifications == {
            "17": {"foo .* bar": ["13"]},
            "42": {},
        }
        assert self.saved_users == {"13": "Graham Chapman"}

    def test_remove_empty(self):
        notifications = self.notifications
        assert notifications.remove_matching(17, r".*", 13) == []
        assert notifications.remove_matching(999, r".*", 13) == []

    def test_remove_wrong_room(self):
        notifications = self.notifications
        notifications.add(17, r"foo .* bar", 13, "Graham Chapman")

        assert notifications.remove_matching(42, r".*", 13) == []
        assert self.saved_notifications == {
            "17": {"foo .* bar": ["13"]},
            "42": {},
        }

    def test_remove_shared_pattern(self):
        notifications = self.notifications
        notifications.add(17, r"foo .* bar", 13, "Graham Chapman")
        notifications.add(17, r"foo .* bar", 23, "Terry Gilliam")
        notifications.add(17, r"foo spam bar", 23, "Terry Gilliam")

        assert notifications.remove_matching(17, r".*", 13) == ["foo .* bar"]
        assert self.saved_notifications == {
            "17": {"foo .* bar": ["23"], "foo spam bar": ["23"]},
            "42": {},
        }

    def test_remove_exact_match(self):
        notifications = self.notifications
        notifications.add(17, r"Monty (Python|Hall)", 13, "Graham Chapman")
        notifications.add(17, r"foo .* bar", 13, "Graham Chapman")

        assert notifications.remove_matching(17, r"Monty (Python|Hall)", 13) == [
            "Monty (Python|Hall)"
        ]
        assert self.saved_notifications == {
            "17": {"foo .* bar": ["13"]},
            "42": {},
        }

    def test_remove_multiple(self):
        notifications = self.notifications
        notifications.add(17, r"Monty (Python|Hall)", 13, "Graham Chapman")
        notifications.add(17, r"foo .* bar", 13, "Graham Chapman")
        notifications.add(17, r"(PYTHON|RUBY)", 13, "Graham Chapman")

        assert sorted(notifications.remove_matching(17, r"python", 13)) == [
            "(PYTHON|RUBY)",
            "Monty (Python|Hall)",
        ]

    def test_remove_duplicate_user_only(self):
        # list the same user more than once for a pattern
        # one of two variants: with no other users there
        with self.filepath.open("w", encoding="utf8") as f:
            json.dump(
                [{"17": {"pattern": ["13", "13", "13"]}}, {"13": "Graham Chapman"},], f,
            )
        self.create_notifications()
        notifications = self.notifications
        notifications.remove_matching(17, r"pattern", 13) == ["pattern"]

        assert self.saved_notifications == {"17": {}, "42": {}}

    def test_remove_duplicate_user_shared(self):
        # list the same user more than once for a pattern
        # one of two variants: with another user there
        with self.filepath.open("w", encoding="utf8") as f:
            json.dump(
                [
                    {"17": {"pattern": ["13", "23", "13", "13"]}},
                    {"13": "Graham Chapman", "23": "Terry Gilliam"},
                ],
                f,
            )
        self.create_notifications()
        notifications = self.notifications
        notifications.remove_matching(17, r"pattern", 13) == ["pattern"]

        assert self.saved_notifications == {"17": {"pattern": ["23"]}, "42": {}}

    def test_filter_empty(self):
        notifications = self.notifications

        post = "Lorum ipsum dolor"
        assert notifications.filter_post(17, post) == post
        assert notifications.filter_post(42, post) == post
        assert notifications.filter_post(999, post) == post

    def test_filter_post_room(self):
        notifications = self.notifications
        notifications.add(17, r"[Ll]\w+ ipsum", 13, "Graham Chapman")
        notifications.add(17, r".*", 83, "Terry Gilliam")
        notifications.add(17, r"Knights of .*", 97, "John Cleese")
        notifications.add(42, r".*", 31, "Eric Idle")
        notifications.add(42, r"Lorum .*", 23, "Michael Palin")

        post = "Lorum ipsum dolor"
        msg = notifications.filter_post(17, post)
        assert msg.startswith(post)
        assert sorted(msg[len(post) :].split()) == ["@GrahamChapman", "@TerryGilliam"]
        msg = notifications.filter_post(42, post)
        assert msg.startswith(post)
        assert sorted(msg[len(post) :].split()) == ["@EricIdle", "@MichaelPalin"]


class _CommandsTestsBase(_NotificationsTestsBase):
    def dispatch(self, content, room=17, user_id=13, user_name="Graham Chapman"):
        """Simulate BotpySE's command handling for tests"""
        from Notifications import CommandNotify, CommandNotifications, CommandUnnotify

        commands = {
            c.usage()[0].split(None, 1)[0]: c
            for c in (CommandNotify, CommandNotifications, CommandUnnotify)
        }

        # BotpySE lowercases messages when building the argument list
        cmd, *arguments = content.lower().split()

        # mock out a command manager, user, room and message object
        command_manager = mock.Mock(notifications=self.notifications)
        user = mock.Mock(id=user_id)
        user.configure_mock(name=user_name)  # can't set name any other way
        message = mock.Mock(user=user, room=mock.Mock(id=room), content=content)

        # capture responses sent via Command.post and Command.reply
        output = SimpleNamespace(reply=[], post=[])
        message.message.reply.side_effect = lambda t, **k: output.reply.append(t)
        message.room.send_message.side_effect = lambda t, **k: output.post.append(t)

        commands[cmd](command_manager, message, arguments).run()

        return output


class TestCommands(_CommandsTestsBase):
    def test_notifications_empty(self):
        response = "    | User   | Regex   |\n    |--------+---------|"
        assert self.dispatch("notifications").post == [response]
        assert self.dispatch("notifications", room=42).post == [response]

    def test_list_filtered(self):
        notifications = self.notifications
        notifications.add(17, r"foo .* bar", 13, "Graham Chapman")
        notifications.add(42, r"Monty (Python|Hall)", 23, "Terry Gilliam")

        output = self.dispatch("notifications")
        assert output.post[0].splitlines()[2:] == [
            "    | Graham Chapman | foo .* bar |"
        ]

    def test_notify_case_sensitive(self):
        pat = "pat  with  spacing and UPPERCASE"
        output = self.dispatch(f"notify {pat}")
        assert output.reply == [f"Added notification for Graham Chapman for {pat}"]
        assert self.saved_notifications == {"17": {pat: ["13"]}, "42": {}}

    def test_notify_invalid_pattern(self):
        pat = "(pat incomplete"
        output = self.dispatch(f"notify {pat}")
        assert output.reply == [
            f"Could not add notification {pat}: "
            "missing ), unterminated subpattern at position 0"
        ]

    def test_notify_existing(self):
        pat = ".*"
        self.notifications.add(17, pat, 13, "Graham Chapman")
        output = self.dispatch(f"notify {pat}")
        assert output.reply == [f"Pattern {pat} already registered for Graham Chapman"]

    def test_notify_normalised(self):
        pat = "Euro: \u20AC"
        pat_html = "<code>Euro: &euro;</code>"
        output = self.dispatch(f"notify {pat_html}")
        assert output.reply == [f"Added notification for Graham Chapman for {pat}"]

        output = self.dispatch(f"notify {pat}")
        assert output.reply == [f"Pattern {pat} already registered for Graham Chapman"]

        output = self.dispatch(f"notify {pat_html}")
        assert output.reply == [f"Pattern {pat} already registered for Graham Chapman"]

        output = self.dispatch("notify <code>(</code>")
        assert output.reply == [
            "Could not add notification (: "
            "missing ), unterminated subpattern at position 0"
        ]

    def test_unnotify_missing(self):
        pat = "foo .* bar"
        output = self.dispatch(f"unnotify {pat}")
        assert output.reply == [f"No matches on {pat} for Graham Chapman"]

    def test_unnotify_invalid_pattern(self):
        pat = "(pat incomplete"
        output = self.dispatch(f"unnotify {pat}")
        assert output.reply == [
            f"Could not remove notification {pat}: "
            "missing ), unterminated subpattern at position 0"
        ]

    def test_unnotify_case_sensitivity(self):
        # this pattern would not match itself, so would only match as literal text
        pat1 = r"^pat \w with  spacing and UPPERCASE"
        # this pattern is going to be matched with a case-insensitive general search
        pat2 = r"foo .* BAR"
        self.notifications.add(17, pat1, 13, "Graham Chapman")
        self.notifications.add(17, pat2, 13, "Graham Chapman")

        output = self.dispatch(f"unnotify {pat1}")
        assert output.reply == [f"Removed notifications: {pat1}"]

        output = self.dispatch(f"unnotify ^foo.*bar$")
        assert output.reply == [f"Removed notifications: {pat2}"]

    def test_unnotify_normalised(self):
        pat = "Euro: \u20AC"
        self.notifications.add(17, pat, 13, "Graham Chapman")

        pat_html = "<code>Euro: &euro;</code>"
        output = self.dispatch(f"unnotify {pat_html}")
        assert output.reply == [f"Removed notifications: {pat}"]

        output = self.dispatch(f"unnotify {pat_html}")
        assert output.reply == [f"No matches on {pat} for Graham Chapman"]

        output = self.dispatch("unnotify <code>(</code>")
        assert output.reply == [
            "Could not remove notification (: "
            "missing ), unterminated subpattern at position 0"
        ]

    def test_command_logging(self):
        self.dispatch("notifications", room=42, user_id=19)
        self.dispatch("notify ^\\w+", room=17, user_id=23)
        self.dispatch("unnotify ^\\w+", room=81, user_id=31)
        assert self.logs.record_tuples == [
            ("Notifications", logging.INFO, "NOTIFICATIONS by 19 in 42"),
            ("Notifications", logging.INFO, "NOTIFY 23 in 17 for ^\\w+"),
            ("Notifications", logging.INFO, "UNNOTIFY ^\\w+ for 31 in 81"),
        ]

    @mock.patch("Notifications.Notifications.add")
    def test_exception(self, add_mock):
        """Introduce an exception in notifications.add and verify it is handled"""
        exc = ValueError("mocked exception")
        add_mock.side_effect = exc
        command = "notify foo .* bar"
        output = self.dispatch(command)
        assert output.reply == [
            f"Oops, the {command} command encountered a problem: {exc!r}"
        ]

        assert [r.levelno for r in self.logs.records] == [logging.INFO, logging.ERROR]
        assert self.logs.records[1].msg == "CommandNotify.run(*(), **{}) failed"
        assert self.logs.records[1].exc_info[:2] == (type(exc), exc)


def _wait_for(threads, timeout):
    """wait *timeout* seconds for threads to exit

    Returns True if all threads have exited, False otherwise.
    """
    end = time.monotonic() + timeout
    while time.monotonic() < end and any(t.is_alive() for t in threads):
        for thread in threads:
            thread.join(0.1)
    return not any(t.is_alive() for t in threads)


class TestThreading(_CommandsTestsBase):
    """Stress-test the commands and see if the final state is consistent.

    This test can't definitively prove thread-safety but *should* fail if
    there are problems, most of the time. You can verify that the test
    fails if there is no thread-safity by using:

        pytest -k test_threading --disable-notification-locking

    """

    THREADCOUNT = 23
    TIMEOUT = 2.0  # seconds

    _exit = threading.Event()

    def runner(self, tid, exception_queue, *commands):
        for command in commands:
            if self._exit.is_set():
                return
            try:
                self.dispatch(**command)
            except Exception as exc:
                exception_queue.put((tid, command, exc))
                return

    def test_threading(self):
        # the command logging is rather noisy if the test fails, without
        # adding anything useful.
        self.logs.set_level(logging.CRITICAL, logger="Notifications")

        # set up definitions for a few users and rooms to generate commands with
        users = SimpleNamespace(
            gc={"user_id": 13, "user_name": "Graham Chapman"},
            mp={"user_id": 23, "user_name": "Michael Palin"},
            ei={"user_id": 31, "user_name": "Eric Idle"},
            tg={"user_id": 83, "user_name": "Terry Gilliam"},
            jc={"user_id": 97, "user_name": "John Cleese"},
        )
        rooms = [{"room": 17}, {"room": 42}]

        # series of arguments for _CommandsTestsBase.dispatch
        commands = [
            {**rooms[0], **users.tg, "content": "notifications"},
            {**rooms[1], **users.jc, "content": "unnotify ^foobar$"},
            {**rooms[0], **users.tg, "content": "notify ^foo .* bar$"},
            {**rooms[0], **users.ei, "content": "notify ^spammy.*$"},
            {**rooms[0], **users.gc, "content": "notifications"},
            {**rooms[1], **users.ei, "content": "notify barry*"},
            {**rooms[1], **users.jc, "content": "notify barry*"},
            {**rooms[1], **users.jc, "content": "notify ^\\w+$"},
            {**rooms[0], **users.tg, "content": "notify ^spammy.*$"},
            {**rooms[0], **users.mp, "content": "notifications"},
            {**rooms[0], **users.mp, "content": "notify \\b[45]/5\\b"},
            {**rooms[0], **users.gc, "content": "notifications"},
            {**rooms[0], **users.tg, "content": "notifications"},
            {**rooms[1], **users.ei, "content": "notify ^\\w+$"},
            {**rooms[1], **users.ei, "content": "unnotify barry*"},
            {**rooms[1], **users.jc, "content": "unnotify ^foobar$"},
            {**rooms[1], **users.gc, "content": "notify barbaz \\b[34]/6\\b"},
            {**rooms[0], **users.ei, "content": "notify ^spammy.*$"},
            {**rooms[1], **users.ei, "content": "notifications"},
            {**rooms[1], **users.jc, "content": "unnotify ^foo.*$"},
            {**rooms[1], **users.mp, "content": "unnotify ."},
        ] * 29

        exception_queue = SimpleQueue()
        minsize, remainder = divmod(len(commands), self.THREADCOUNT)
        threads = []
        for i in range(self.THREADCOUNT):
            tid = f"runner-{i}"
            size = minsize + (1 if i < remainder else 0)
            args = (tid, exception_queue, *commands[i : i + size])
            # threads are marked as daemon threads so a deadlocked thread never
            # holds up the test.
            thread = threading.Thread(
                target=self.runner, args=args, name=tid, daemon=True
            )
            threads.append(thread)
            thread.start()

        if not _wait_for(threads, self.TIMEOUT):
            # test failed, threads didn't complete in the timeout.
            # Attempt to recover by setting the exit event, then waiting another few
            # seconds. This is just a courtesy at this point, as daemon threads won't
            # block Python from exiting.
            self._exit.set()
            _wait_for(threads, 3)
            pytest.fail("Threads didn't complete", False)

        if not exception_queue.empty():
            lines = ["One or more messages triggered an exception:\n"]
            while not exception_queue.empty():
                tid, command, exc = exception_queue.get(False)
                lines.append(f"\nThread: {tid}\nCommand: {command}\n")
                lines += traceback.format_exception(None, exc, exc.__traceback__)
                del exc  # clear exception to avoid leaks

            pytest.fail("".join(lines), False)

        assert self.saved_notifications == {
            "17": {
                "\\b[45]/5\\b": ["23"],
                "^foo .* bar$": ["83"],
                "^spammy.*$": ["31", "83"],
            },
            "42": {
                "^\\w+$": ["97", "31"],
                "barbaz \\b[34]/6\\b": ["13"],
                "barry*": ["97"],
            },
        }

        assert self.saved_users == {
            str(u["user_id"]): u["user_name"] for u in vars(users).values()
        }
