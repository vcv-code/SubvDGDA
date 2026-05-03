FROM python:3.12-slim

RUN pip install --no-cache-dir requests pymysql

RUN mkdir -p /app/logs/cron /app/scripts

COPY scripts/    /app/scripts/
COPY scheduler.py /app/scheduler.py

CMD ["python3", "/app/scheduler.py"]
