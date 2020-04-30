import pytest
from contextlib import nullcontext
from unittest import mock


def pytest_addoption(parser, pluginmanager):
    parser.addoption(
        "--disable-notification-locking",
        dest="testthreading_disable_locking",
        action="store_true",
        default=False,
        help="Neuter the lock used in Notifications to help the threading tests fail",
    )


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_setup(item):
    ctx = nullcontext()
    if (
        item.config.option.testthreading_disable_locking
        and isinstance(item, pytest.Function)
        and item.parent.nodeid == "tests/test_notifications.py::TestThreading"
    ):
        # make failure all but certain by replacing the lock with a no-op.
        ctx = mock.patch("Notifications.Lock", nullcontext)

    with ctx:
        _ = yield
