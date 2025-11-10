# Бот регистрации на мероприятие

## Запуск
Требуется `docker`.

```shell
docker compose -f docker-compose.yaml --env-file .env up --build
```

Окружение загружается из `.env`. Обязательные переменные:
- `TELEGRAM_BOT_TOKEN` — токен бота
- `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` — для контейнера БД (см. docker-compose)
- опционально: `DATABASE_URI` (по умолчанию локальная строка подключения)
