FROM python:3.12-slim

RUN pip install flask docker

COPY app.py /app.py

CMD ["python", "/app.py"]
