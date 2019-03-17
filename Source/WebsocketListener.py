#
# WebsocketListener.py
# PulseMonitor
#
# Created by Ashish Ahuja on 24th September 2017.
# This file is licensed under the MIT License.
#

import threading
import logging

import websocket


class WebsocketListener:
    def __init__(self, websocket_link, on_message_callback, notifications=None):
        self.websocket_link = websocket_link
        self.on_message_callback = on_message_callback
        self.notifications = notifications
        self.closed = True

    def on_error(self, ws, error):
        logging.error("A websocket error occurred on websocket '{0}':".format(
            self.websocket_link))
        logging.error(error)

    def on_close(self, ws):
        self.closed = True
        print( "The websocket with link '{0}' was closed.".format(
            self.websocket_link))

    def start(self):
        self.closed = False
        websocket.enableTrace(True)
        ws = websocket.WebSocketApp(
            self.websocket_link,
            on_error=self.on_error,
            on_close=self.on_close,
            on_message=self.on_message_callback)
        ws_thread = threading.Thread(target = ws.run_forever)
        ws_thread.start()
        self.ws = ws
        self.ws_thread = ws_thread

    def stop(self):
        self.closed = True
        self.ws.keep_running = False
