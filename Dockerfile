FROM python:3.10-slim

VOLUME /app/data
EXPOSE 8881

COPY requirements.txt /tmp/
RUN --mount=type=cache,target=/root/.cache pip install --prefer-binary -r /tmp/requirements.txt

COPY api.py /app/
WORKDIR /app

CMD ["python", "api.py"]
