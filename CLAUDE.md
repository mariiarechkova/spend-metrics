# Spendmetrics — контекст для Claude Code

## Что это

Платформа аналитики рекламы для малого бизнеса. Собирает заявки из всех каналов (сайт, Telegram, VK, Meta) и расходы из рекламных кабинетов (Яндекс Директ, VK Ads, Meta Ads), считает CPL по каждому каналу и кампании.

Целевая аудитория — микробизнес СНГ: онлайн-школы, эксперты, коучи.

---

## Архитектура

```
Заявки (webhook, Telegram-бот, VK Lead Ads, Meta Lead Ads)
    → FastAPI → ClickHouse

Рекламные расходы (Яндекс, VK, Meta)
    → n8n (по расписанию ночью) → FastAPI → ClickHouse

ClickHouse → Grafana (бизнес-дашборды)
FastAPI → Prometheus → Grafana (мониторинг)
FastAPI → n8n (уведомления и алерты в Telegram)
```

**Две базы данных — разные роли:**
- **PostgreSQL** — операционные данные: пользователи, OAuth токены, настройки, подписки
- **ClickHouse** — аналитика: заявки, рекламные расходы, метрики приложения

**n8n — оркестратор**, не Celery. Синхронизация по расписанию и алерты живут там.

**Мультитенантность** — каждый запрос к ClickHouse фильтруется по `user_id`.

---

## Стек

| Компонент | Технология |
|---|---|
| Бэкенд | FastAPI + Python 3.12 |
| PostgreSQL клиент | SQLAlchemy 2.0 async + asyncpg |
| ClickHouse клиент | clickhouse-connect (HTTP, порт 8123) |
| Миграции | Alembic (async) |
| Валидация | Pydantic v2 + pydantic-settings |
| JWT | python-jose + HS256 |
| Пароли | passlib bcrypt |
| Метрики | prometheus-fastapi-instrumentator |
| Тесты | pytest + pytest-asyncio + pytest-httpx |

**Важно для ClickHouse:** используется HTTP интерфейс (порт 8123), не нативный (9000). Клиент — `clickhouse_connect`, не `clickhouse-driver`.

---

## Структура проекта

```
spend-metrics/
├── CLAUDE.md
├── docker-compose.yml
├── prometheus.yml
├── backend/
│   ├── .env
│   ├── .env.example
│   ├── alembic.ini
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── migrations/
│   └── app/
│       ├── main.py
│       ├── api/            # auth.py, webhook.py, oauth.py, sync.py, stats.py, alerts.py, billing.py
│       ├── core/           # config.py, security.py, dependencies.py
│       ├── db/             # postgres.py, clickhouse.py
│       ├── models/
│       │   ├── postgres/   # user.py, ad_connection.py, lead_source.py, subscription.py
│       │   └── clickhouse/ # lead.py, ad_spend.py
│       └── services/       # yandex.py, vk.py, meta.py, telegram.py, stripe.py
```

---

## Соглашения по коду

- **Async везде** в FastAPI и SQLAlchemy. ClickHouse клиент синхронный — оборачивать в `asyncio.to_thread()` при вызове из async контекста.
- **SQLAlchemy 2.0** — `Mapped[T]` и `mapped_column()`, не `Column()`.
- **Pydantic v2** — `model_config = ConfigDict(...)`, не `class Config`.
- **UUID** — тип `uuid.UUID` в Python, `UUID(as_uuid=True)` в SQLAlchemy, строка при вставке в ClickHouse.
- **Никаких хардкодных значений** — всё через `settings` из `app.core.config`.
- **Комментарии** — только когда WHY неочевиден. Не описывать что делает код.

---

## Команды для разработки

```bash
# Поднять все сервисы
docker-compose up --build

# Только инфраструктура (без бэкенда)
docker-compose up postgres clickhouse redis n8n grafana prometheus

# Применить миграции
docker-compose exec backend alembic upgrade head

# Создать новую миграцию
docker-compose exec backend alembic revision --autogenerate -m "название"

# Запустить тесты
docker-compose exec backend pytest

# Логи бэкенда
docker-compose logs -f backend
```

---

## Документация

- `spendmetrics_plan.md` — полное продуктовое ТЗ: схемы БД, API эндпоинты, n8n флоу, план по неделям
- `weekN_*_plan.md` — детальный план реализации каждой недели с кодом
