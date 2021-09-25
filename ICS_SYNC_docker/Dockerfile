FROM python:3.9.6
COPY requirements.txt /root/
RUN pip install -r /root/requirements.txt
RUN mkdir /app
WORKDIR /app
COPY ["token files", "/app/token files"]
COPY converter.py creds.json Google.py main.py /app/
ENTRYPOINT ["python", "-u", "main.py"]
