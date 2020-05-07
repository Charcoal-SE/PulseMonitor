import json
import logging
import re
import time
import threading
import traceback
from itertools import product
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
        notifications.add(42, r"foo .* bar", 13, "Graham Chapman")
        notifications.add(42, r"Monty (Python|Hall)", 23, "Terry Gilliam")

        assert list(notifications.list(room=17)) == [
            ("17", "foo .* bar", "13", "Graham Chapman")
        ]
        assert list(notifications.list(room=42)) == [
            ("42", "foo .* bar", "13", "Graham Chapman"),
            ("42", "Monty (Python|Hall)", "23", "Terry Gilliam"),
        ]

        assert list(notifications.list(user=13)) == [
            ("17", "foo .* bar", "13", "Graham Chapman"),
            ("42", "foo .* bar", "13", "Graham Chapman"),
        ]
        assert list(notifications.list(user=23)) == [
            ("42", "Monty (Python|Hall)", "23", "Terry Gilliam"),
        ]

        assert list(notifications.list(room=42, user=13)) == [
            ("42", "foo .* bar", "13", "Graham Chapman"),
        ]

        assert list(notifications.list(room=9999)) == []
        assert list(notifications.list(room=9999, user=13)) == []
        assert list(notifications.list(user=9999)) == []
        assert list(notifications.list(room=42, user=9999)) == []

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


# extract just the word groups at the start
_clean_usage = re.compile(r'^(?:\w+[ ])*\w+').search


class _CommandsTestsBase(_NotificationsTestsBase):
    def dispatch(self, content, room=17, user_id=13, user_name="Graham Chapman"):
        """Simulate BotpySE's command handling for tests"""
        from Notifications import NotificationsCommandBase

        commands = {
            _clean_usage(usage)[0]: c
            for c in NotificationsCommandBase.__subclasses__()
            for usage in c.usage()
        }

        # BotpySE lowercases messages when building the argument list
        cmd, *arguments = content.lower().split()

        # Handle commands with more than one word
        while arguments and cmd not in commands:
            cmd = f"{cmd} {arguments.pop(0)}"

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
        assert self.dispatch("all notifications").post == [response]
        assert self.dispatch("all notifications", room=42).post == [response]

    def test_notifications_filtered(self):
        notifications = self.notifications
        notifications.add(17, r"foo .* bar", 13, "Graham Chapman")
        notifications.add(42, r"Monty (Python|Hall)", 23, "Terry Gilliam")

        output = self.dispatch("notifications")
        assert output.post[0].splitlines()[2:] == [
            "    | Graham Chapman | foo .* bar |"
        ]

        assert self.dispatch("all notifications").post == output.post

    def test_my_notifications_empty(self):
        response = (
            "    | Graham Chapman   |\n"
            "    | Regex            |\n"
            "    |------------------|"
        )
        assert self.dispatch("my notifications").post == [response]
        assert self.dispatch("my notifications", room=42).post == [response]

    def test_my_notifications_filtered(self):
        notifications = self.notifications
        notifications.add(17, r"foo .* bar", 13, "Graham Chapman")
        notifications.add(17, r"^spammy.*$", 97, "John Cleese")
        notifications.add(42, r"foo", 23, "Terry Gilliam")

        output = self.dispatch("my notifications")
        lines = output.post[0].splitlines()
        assert lines[0] == "    | Graham Chapman   |"
        assert lines[3:] == [
            "    | foo .* bar       |"
        ]

    def test_notify_case_sensitive(self):
        pat = "pat  with  spacing and UPPERCASE"
        output = self.dispatch(f"notify {pat}")
        assert output.reply == [f"Added notification for Graham Chapman for `{pat}`"]
        assert self.saved_notifications == {"17": {pat: ["13"]}, "42": {}}

    def test_notify_invalid_pattern(self):
        pat = "(pat incomplete"
        output = self.dispatch(f"notify {pat}")
        assert output.reply == [
            f"Could not add notification `{pat}`: "
            "missing ), unterminated subpattern at position 0"
        ]

    def test_notify_existing(self):
        pat = ".*"
        self.notifications.add(17, pat, 13, "Graham Chapman")
        output = self.dispatch(f"notify {pat}")
        assert output.reply == [
            f"Pattern `{pat}` already registered for Graham Chapman"
        ]

    def test_notify_normalised(self):
        pat = "Euro: \u20AC"
        pat_html = "<code>Euro: &euro;</code>"
        output = self.dispatch(f"notify {pat_html}")
        assert output.reply == [f"Added notification for Graham Chapman for `{pat}`"]

        output = self.dispatch(f"notify {pat}")
        assert output.reply == [
            f"Pattern `{pat}` already registered for Graham Chapman"
        ]

        output = self.dispatch(f"notify {pat_html}")
        assert output.reply == [
            f"Pattern `{pat}` already registered for Graham Chapman"
        ]

        output = self.dispatch("notify <code>(</code>")
        assert output.reply == [
            "Could not add notification `(`: "
            "missing ), unterminated subpattern at position 0"
        ]

    def test_unnotify_missing(self):
        pat = "foo .* bar"
        output = self.dispatch(f"unnotify {pat}")
        assert output.reply == [f"No matches on `{pat}` for Graham Chapman"]

    def test_unnotify_invalid_pattern(self):
        pat = "(pat incomplete"
        output = self.dispatch(f"unnotify {pat}")
        assert output.reply == [
            f"Could not remove notification `{pat}`: "
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
        assert output.reply == [f"Removed notifications: `{pat1}`"]

        output = self.dispatch(f"unnotify ^foo.*bar$")
        assert output.reply == [f"Removed notifications: `{pat2}`"]

    def test_unnotify_normalised(self):
        pat = "Euro: \u20AC"
        self.notifications.add(17, pat, 13, "Graham Chapman")

        pat_html = "<code>Euro: &euro;</code>"
        output = self.dispatch(f"unnotify {pat_html}")
        assert output.reply == [f"Removed notifications: `{pat}`"]

        output = self.dispatch(f"unnotify {pat_html}")
        assert output.reply == [f"No matches on `{pat}` for Graham Chapman"]

        output = self.dispatch("unnotify <code>(</code>")
        assert output.reply == [
            "Could not remove notification `(`: "
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

    To really push the issue, run the test repeatedly:

        pip install pytest-repeat
        pytest -k test_threading --count=100 -x --disable-notification-locking

    """

    THREADCOUNT = 23
    TIMEOUT = 5.0  # seconds

    _exit = threading.Event()

    def runner(self, tid, exception_queue, *commands):
        for command in commands:
            if self._exit.is_set():
                return
            try:
                self.dispatch(**command)
                for r in self.logs.records:
                    if (
                        r.threadName == tid  # triggered by this thread
                        and r.levelno == logging.ERROR  # and it's an error
                    ):
                        exception_queue.put((tid, command, r.exc_info[1]))
                        return
            except Exception as exc:
                exception_queue.put((tid, command, exc))
                return

    def test_threading(self):
        # capture errors in commands
        self.logs.set_level(logging.ERROR, logger="Notifications")

        # set up definitions for a few users and rooms to generate commands with
        users = {
            13: "Graham Chapman",
            23: "Michael Palin",
            83: "Terry Gilliam",
            97: "John Cleese",
        }
        rooms = (17, 42)
        messages = (
            "notify ^foobar$",
            "notifications",
            "notify ^foo .* bar$",
            "notifications",
            "notify ^spammy.*$",
            "notifications",
            "notify barry*",
            "notifications",
            "notify ^\\w+$",
            "notifications",
        )

        # series of arguments for _CommandsTestsBase.dispatch
        commands = [
            {"room": rid, "user_id": uid, "user_name": users[uid], "content": cmd,}
            for cmd, uid, rid in product(messages, users, rooms)
        ]
        # A single pattern registered to a single user causes the
        # notifications[roomid] dictionary to grow and shrink repeatedly
        # which can cause errors if something else is also iterating over
        # the same.
        iuid, iuname = 31, "Eric Idle"
        interference = [
            {"room": rid, "user_id": iuid, "user_name": iuname, "content": c}
            for rid, c in product(
                rooms, ("notify \\b[45]/5\\b", "unnotify \\b[45]/5\\b")
            )
        ] * (len(commands) // 4)

        exception_queue = SimpleQueue()
        # threads are marked as daemon threads so a deadlocked thread never
        # holds up the test.
        threads = [
            threading.Thread(
                target=self.runner,
                args=("notify", exception_queue, *commands),
                name="notify",
                daemon=True,
            ),
            *(
                threading.Thread(
                    target=self.runner,
                    args=(f"interference-{i}", exception_queue, *interference),
                    name=f"interference-{i}",
                    daemon=True,
                )
                for i in range(self.THREADCOUNT - 1)
            ),
        ]

        for t in threads:
            t.start()

        if not _wait_for(threads, self.TIMEOUT):
            # test failed, threads didn't complete in the timeout.
            # Attempt to recover by setting the exit event, then waiting another few
            # seconds. This is just a courtesy at this point, as daemon threads won't
            # block Python from exiting.
            self._exit.set()
            _wait_for(threads, 3)
            pytest.fail("Threads didn't complete", False)

        # any issues with errors will have been reported by the thread runner
        # so no need to report twice.
        self.logs.clear()

        if not exception_queue.empty():
            lines = ["One or more messages triggered an exception:\n"]
            while not exception_queue.empty():
                tid, command, exc = exception_queue.get(False)
                lines.append(f"\nThread: {tid}\nCommand: {command}\n")
                lines += traceback.format_exception(None, exc, exc.__traceback__)
                del exc  # clear exception to avoid leaks

            pytest.fail("".join(lines), False)

        patterns = [p[7:] for p in messages if p != "notifications"]
        assert {
            rid: {p: sorted(users) for p, users in pat.items()}
            for rid, pat in self.saved_notifications.items()
        } == {
            str(rid): {pat: [str(uid) for uid in sorted(users)] for pat in patterns}
            for rid in rooms
        }

        users[iuid] = iuname  # the interference user also registered
        assert self.saved_users == {
            str(uid): user_name for uid, user_name in users.items()
        }
