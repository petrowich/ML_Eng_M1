# ML Service (Web + Worker + RabbitMQ + PostgreSQL)

Проект состоит из:
- app — веб‑приложение на Python (взаимодействие с пользователем через веб-UI, принимает запросы к ML моделями,
  отправляет сообщения в RabbitMQ для ML‑воркера, рассчитывает стоимость запросов для пользователя).
- worker — воркер(ы) обработки задач (очередь RabbitMQ, выполнение ML-инференса/логики, отправка статуса выполнения
  и результатов в RabbitMQ).
- web-proxy — Nginx (reverse proxy, TLS при необходимости).
- rabbitmq — брокер сообщений (используется rabbitmq:3-management).
- database — PostgreSQL 16.

Запуск и локальная разработка выполняются через docker compose.

---

## Требования

- Docker
- Docker Compose (plugin `docker compose`)

Проверка:
  docker --version
  docker compose version

---

## Структура репозитория

    ├── app/
    │   ├── Dockerfile
    │   └── src/
    │       ├── .env
    │       └── ...
    ├── worker/
    │   ├── Dockerfile
    │   └── src/
    │       ├── .env
    │       └── ...
    ├── web-proxy/
    │   ├── Dockerfile
    │   └── nginx.conf
    ├── docker-compose.yaml
    └── README.md

---

## Конфигурация окружения

### 1) Переменные PostgreSQL (compose-level)

Сервис database использует переменные:
- POSTGRES_USER
- POSTGRES_PASSWORD
- POSTGRES_DB

файл ./.env (в корне репозитория):
  POSTGRES_USER=postgres
  POSTGRES_PASSWORD=postgres
  POSTGRES_DB=ml_service

Примечание: это другой .env, не тот, что подключается как env_file в app/src/.env и worker/src/.env.

### 2) Переменные приложения и воркера

В docker-compose.yaml подключены:

    - app/src/.env
    - worker/src/.env

---

## Запуск

Сборка и запуск:

    docker compose up -d --build

Остановка:

    docker compose down

---

## Доступные сервисы и порты

### Nginx (входная точка)
- http://localhost/  (порт 80)

### RabbitMQ
- AMQP: localhost:5672
- Management UI: http://localhost:15672
  По умолчанию логин/пароль: guest / guest (если не переопределено)

### PostgreSQL
- localhost:5432

---

## Важно

### Worker replicas

В docker-compose.yaml указывается количество воркеров:
 
      worker:    
         deploy:    
          replicas: 3

Если нужно n воркеров в обычном compose:

    docker compose up -d --build --scale worker=n

---

