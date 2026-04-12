FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt /app/
RUN apt-get update && apt-get install -y curl
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt
COPY src/ /app/
EXPOSE 8080
CMD ["python", "api.py"]