FROM python:3.6.6-alpine3.7

COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY GetTempSensor.py /GetTempSensor.py

CMD ["python3", "-u", "/GetTempSensor.py"]
