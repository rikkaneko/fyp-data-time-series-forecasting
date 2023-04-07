FROM python:3.10-slim

VOLUME /app/data
EXPOSE 8881

COPY requirements.txt /tmp/
RUN pip install --no-cache-dir --prefer-binary -r /tmp/requirements.txt

COPY api.py /app/
WORKDIR /app

CMD ["python", "api.py"]
