# PulseMonitor

To run PulseMonitor, you need to have the packages BotpySE and chatexchange
installed on your computer.

You will probably want to install chatexchange from source.
Older versions have bugs which prevent PulseMonitor from working properly.
(Unfortunately, a properly versioned dependency cannot yet be specified.)

    git clone https://github.com/Manishearth/ChatExchange
    pip install $(pwd)/ChatExchange
    pip install -r requirements.txt 

Once that is done, copy the privileged user file to a directory in your home directory
named `.pulsemonitor`.

    mkdir ~/.pulsemonitor
    cp room_*_privileged_users ~/.pulsemonitor/

You might want to add yourself as a privileged user. Load the file
with `pickle`, change one of the user ID:s to your own, and save back
and overwrite the pickle file.

To enable Redunda, paste your redunda key in a file called `redunda_key.txt` at `~/.pulsemonitor/`.

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
    pulse> @you Active notification: tripleee '[23]/3'
	you> @pulse notify .*
	pulse> @you Added notification for you for '.*'
	you> @pulse unnotify .
	pulse> @you Removed notifications ['.*']

Notice that the argument to `unnotify` can be substring which matches
more than one active pattern. You can only add and remove your own notifications.

The notification mechanism simply pings @you when a matching line is printed to
the chat transcript.
