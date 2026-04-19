FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt /app/
RUN apt-get update && apt-get install -y curl
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt
COPY src/ /app/
CMD ["celery", "-A", "celery_app", "worker", "--loglevel=info"]