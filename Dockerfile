FROM python:3.11-slim

WORKDIR /app
COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:8080", "app:app", "--log-level", "debug", "--access-logfile", "-", "--error-logfile", "-"]

