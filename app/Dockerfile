FROM python:3.10-alpine
WORKDIR /app
COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt
COPY src/ /app/
EXPOSE 8080
CMD ["python", "main.py"]