FROM frolvlad/alpine-python3:latest

RUN apk add --no-cache git && \
    : "install dependencies which need compilation from packages" && \
    apk add --no-cache py3-greenlet && \
    adduser -D pulsemonitor && \
    cd /home/pulsemonitor && \
    su pulsemonitor sh -c 'mkdir .pulsemonitor' && \
    git clone https://github.com/Manishearth/ChatExchange && \
    : "######## TODO: replace with official repo" && \
    git clone https://github.com/tripleee/PulseMonitor && \
    pip install /home/pulsemonitor/ChatExchange && \
    : "######## FIXME: BotpySE requirements not yet declared in PyPi" && \
    pip install tabulate && \
    pip install -r /home/pulsemonitor/PulseMonitor/requirements.txt && \
    rm -rf /var/cache/apk/*

ADD room_65945_name_Charcoal_Test_privileged_users /home/halflife/.pulsemonitor/
ADD run /home/pulsemonitor/run
#ADD docker-cron-15min /etc/periodic/15min/git-pull-sd

#EXPOSE 8888

CMD ["su", "-", "pulsemonitor", "/home/pulsemonitor/run"]
