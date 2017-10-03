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

Then run the `startup.py` file.

    python3 ./Source/startup.py

It will ask you for the account email and password for running the bot.
To avoid manual interaction, you can define these in the environment variables
`PulseEmail` and `PulsePass`, respectively.
The account (obviously) needs to have the necessary privileges to participate in
the chat room.
