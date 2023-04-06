FROM python:3.10-slim

VOLUME /app/data
EXPOSE 8881

COPY api.py requirements.txt /app/
WORKDIR /app

RUN pip install --no-cache-dir --prefer-binary -r requirements.txt

CMD ["python", "api.py"]
