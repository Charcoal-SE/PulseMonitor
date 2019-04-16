FROM frolvlad/alpine-python3:latest

RUN apk add --no-cache git && \
    : "install dependencies which need compilation from packages" && \
    apk add --no-cache py3-greenlet && \
    adduser -D pulsemonitor && \
    cd /home/pulsemonitor && \
    su pulsemonitor sh -c 'mkdir .pulsemonitor && \
      git clone https://github.com/tripleee/PulseMonitor && \
      cd PulseMonitor && \
      git checkout send-aggressively' && \
    cd PulseMonitor && \
    pip install -r requirements.txt && \
    rm -rf /var/cache/apk/*

ADD --chown=pulsemonitor:pulsemonitor room_65945_name_Charcoal_Test_privileged_users /home/pulsemonitor/.pulsemonitor/
ADD --chown=pulsemonitor:pulsemonitor redunda_key.txt /home/pulsemonitor/.pulsemonitor/
ADD run.prod /home/pulsemonitor/run.prod
#ADD docker-cron-15min /etc/periodic/15min/git-pull-sd

USER pulsemonitor
CMD ["/home/pulsemonitor/run.prod"]
