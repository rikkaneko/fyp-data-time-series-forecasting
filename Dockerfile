FROM python:3.10-slim

VOLUME /app/data
EXPOSE 8881

COPY requirements.txt /tmp/
RUN --mount=type=cache,target=/root/.cache pip install --prefer-binary -r /tmp/requirements.txt

# Create non-root user
RUN useradd -u 1000 user

COPY --chmod=744 api.py /app/
WORKDIR /app

USER user

CMD ["python", "api.py"]
