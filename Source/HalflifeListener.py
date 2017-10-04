#
# HalflifeListener.py
# PulseMonitor
#
# Created by Ashish Ahuja on 25th September 2017.
# This file is licensed under the MIT License.
#

from WebsocketListener import WebsocketListener

class HalflifeListener:
    def __init__(self, error_room, report_rooms):
        self.error_room = error_room
        self.report_rooms = report_rooms
        self.ws_link = "ws://ec2-52-208-37-129.eu-west-1.compute.amazonaws.com:8888/"
        self.ws_listener = WebsocketListener(self.ws_link, self.on_message_handler)

    def on_message_handler(self, ws, message):
        for each_room in self.report_rooms:
            each_room.send_message(message)

    def start(self):
        self.ws_listener.start()

    def stop(self):
        self.ws_listener.stop()
