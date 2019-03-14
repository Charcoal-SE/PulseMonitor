# PulseMonitor

This is the chatbot component of Halflife.  It is currently running on the
[Halflife bot account](https://chat.stackexchange.com/users/389741/halflife).

To run PulseMonitor, you need to have the packages BotpySE and chatexchange
installed on your computer.

Once that is done, copy the privileged user file to a directory
in your home directory
named `.pulsemonitor`.

    mkdir ~/.pulsemonitor
    cp room_*_privileged_users ~/.pulsemonitor/

You might want to add yourself as a privileged user. Load the file
with `pickle`, change one of the user ID:s to your own, and save back
and overwrite the pickle file.

To enable Redunda, paste your redunda key
in a file called `redunda_key.txt` at `~/.pulsemonitor/`.

Then run the `startup.py` file.

    python3 ./Source/startup.py

It will ask you for the account email and password for running the bot.
To avoid manual interaction, you can define these in the environment variables
`PulseEmail` and `PulsePass`, respectively.
The account (obviously) needs to have the necessary privileges to participate in
the chat room.

The bot has commands to add, review, and remove notifications by
regex. Here's a quick example.

    you> @pulse notifications
    pulse> @you Active notification: someone 'foobar'
    you> @pulse notify .*
    pulse> @you Added notification for you for '.*'
    you> @pulise notifications
    pulse> @you Active notification: someone 'foobar'
    pulse> @you Active notification: you '.*'
    you> @pulse unnotify .
    pulse> @you Removed notifications ['.*']

    you> @pulse addtag threshold [23]/3
    pulse> @you added [tag:threshold] for regex [23]/3
    you> @pulse removetag nonesvch
    pulse> @you No tag found with regex nonesvch
    you> @pulse listtags
    pulse> | Name        | Regex      | Added by    |
    pulse> |-------------+------------+-------------|
    pulse> | threshold   | [23]/3     | you         |
    pulse> | threshold   | (9|10)/10  | someone     |

Notice that the argument to `unnotify` and `removetag` is a regex
which can match more than one active pattern.
You can only add and remove your own notifications.

Because the Stack Exchange chat interface will do odd things to some
special characters, you can optionally embed the regex
for `notify` and `addtag` in `` `backticks` ``.

The notification mechanism simply pings @you when a matching line is printed to
the chat transcript.
Tagging adds a tag to the transcript which can be searched for
with an expression like
[tagged/tagname](https://chat.stackexchange.com/search?q=tagged%2Fthreshold&user=&room=65945)
