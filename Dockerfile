FROM python:3.12-slim
WORKDIR /app
RUN pip install --no-cache-dir mcp
COPY server.py .
ENV GYMLOG_DB_DIR=/data
VOLUME /data
CMD ["python", "server.py"]
