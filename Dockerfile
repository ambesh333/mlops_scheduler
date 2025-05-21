FROM python:3.12-slim

WORKDIR /app


COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

COPY docker.sh /docker.sh
RUN chmod +x /docker.sh

EXPOSE 8000

ENTRYPOINT ["/docker.sh"]
