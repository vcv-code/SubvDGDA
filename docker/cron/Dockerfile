FROM python:3.12-slim

# supercronic: cron diseñado para contenedores (logs a stdout, sin daemon)
ADD https://github.com/aptible/supercronic/releases/download/v0.2.33/supercronic-linux-amd64 /usr/local/bin/supercronic
RUN chmod +x /usr/local/bin/supercronic

RUN pip install --no-cache-dir requests pymysql

RUN mkdir -p /app/logs/cron /app/scripts

COPY scripts/ /app/scripts/
COPY crontab  /etc/cron/crontab

CMD ["supercronic", "/etc/cron/crontab"]
