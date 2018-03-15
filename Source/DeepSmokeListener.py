#
# DeepSmokeListener.py
# PulseMonitor
#
# Created by Ashish Ahuja on 3rd October 2017.
# This file is licensed under the MIT License.
#

from WebsocketListener import WebsocketListener
import json
import pprint

class DeepSmokeListener:
    def __init__(self, error_room, report_rooms, notifications=None):
        self.error_room = error_room
        self.report_rooms = report_rooms
        self.notifications = notifications
        self.ws_link = "ws://smokey-deepsmoke2903.cloudapp.net:8888/"
        self.ws_listener = WebsocketListener(self.ws_link, self.on_message_handler)
        
    def report(self, message, error_room=False):
        if not error_room:
            for each_room in self.report_rooms:
                if self.notifications is not None:
                    this_message = self.notifications.filter_post(
                        each_room.id, message)
                else:
                    this_message = message
                each_room.send_message(
                    "[ [DeepSmoke](https://git.io/vdlxx) | "
                        "[PM](https://git.io/vdlx5) ] " + this_message)
        else:
            self.error_room.send_message("[ [DeepSmoke](https://git.io/vdlxx) | [PM](https://git.io/vdlx5) ] " + message)

    def get_link(self, data):
        return "https://{0}/q/{1}".format(data["site"], data["question_id"])
       
    def on_message_handler(self, ws, message):
        data = json.loads(message)
       # print("-------------------------------------------")
       # print("               RESTART                     ")
       # print("-------------------------------------------")
       # pprint.pprint(data)
        
        ds = data['deepsmoke'][0]
        ds_response = data['deepsmoke'][1]
        score = ds_response['score']

        print("Post score: " + str(score))

        if ds and score > 0.9 and data['site'] not in [
                "ru.stackoverflow.com", "ja.stackoverflow.com",
                "rus.stackexchange.com"]:
            self.report("Potential spam because of deepsmoke analysis: [" + data['title'] + "]("+ self.get_link(data) + ") on `" + data['site'] + "` with score `" + str(ds_response['score']) + "`")
            return
        elif score > 0.7:
            self.report("Potential spam because of deepsmoke analysis: [" + data['title'] + "]("+ self.get_link(data) + ") on `" + data['site'] + "` with score `" + str(ds_response['score']) + "`", error_room=True)

    def start(self):
        self.ws_listener.start()

    def stop(self):
        self.ws_listener.stop()
