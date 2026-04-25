# Spendmetrics — контекст для Codex

## Что это

Платформа аналитики рекламы для малого бизнеса. Собирает заявки из всех каналов (сайт, Telegram, VK, Meta) и расходы из рекламных кабинетов (Яндекс Директ, VK Ads, Meta Ads), считает CPL по каждому каналу и кампании.

---

## Архитектура

**Две базы данных — разные роли:**
- **PostgreSQL** — операционные данные: пользователи, OAuth токены, настройки, подписки
- **ClickHouse** — аналитика: заявки, рекламные расходы, метрики приложения

**n8n — оркестратор.** Синхронизация по расписанию и алерты живут там, не в Celery и не в APScheduler.

**Мультитенантность** — каждый запрос к ClickHouse фильтруется по `user_id`. Никогда не делать запросы без этого фильтра.

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

**Критично:** ClickHouse использует HTTP интерфейс порт 8123, клиент `clickhouse_connect`. Не использовать `clickhouse-driver` (нативный протокол, порт 9000).

---

## Структура проекта

```
spend-metrics/
├── docker-compose.yml
├── prometheus.yml
├── backend/
│   ├── .env.example
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── alembic.ini
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
- **SQLAlchemy 2.0** — `Mapped[T]` и `mapped_column()`, не старый `Column()`.
- **Pydantic v2** — `model_config = ConfigDict(...)`, не `class Config`.
- **UUID** — `uuid.UUID` в Python, `UUID(as_uuid=True)` в SQLAlchemy, строка при вставке в ClickHouse.
- **Настройки** — только через `settings` из `app.core.config`, никаких хардкодных значений.
- **Комментарии** — только когда WHY неочевиден.

---

## Как проверять работу

Codex работает в изолированной среде без Docker. Проверять изменения так:

```bash
cd backend

# Установить зависимости
pip install -r requirements.txt

# Проверить импорты и синтаксис
python -c "from app.main import app"
python -c "from app.api.auth import router"

# Статический анализ
python -m py_compile app/**/*.py

# Запустить unit-тесты (не требуют БД)
pytest tests/ -v -k "not integration"
```

Тесты которые требуют реальных БД помечать маркером `@pytest.mark.integration` и не запускать в изоляции.

---

## Что нельзя трогать без явного указания

- **`migrations/versions/`** — не создавать и не редактировать файлы миграций. Миграции генерируются командой `alembic revision --autogenerate` после изменения моделей.
- **`docker-compose.yml`** — инфраструктура фиксирована.
- **`.env`** — никогда не создавать и не читать, работать с `.env.example`.
- **`requirements.txt`** — не добавлять зависимости без явного запроса.

---

## Как писать тесты

Моки для изоляции от инфраструктуры:

```python
# PostgreSQL — использовать pytest-asyncio с in-memory SQLite или мокировать get_db
# ClickHouse — мокировать get_clickhouse_client через monkeypatch или unittest.mock
# HTTP клиенты — pytest-httpx для мокирования внешних API

# Пример структуры теста
@pytest.mark.asyncio
async def test_register(async_client):
    response = await async_client.post("/auth/register", json={
        "email": "test@example.com",
        "password": "secret123"
    })
    assert response.status_code == 201
    assert "access_token" in response.json()
```

---

## Документация

- `spendmetrics_plan.md` — полное продуктовое ТЗ: схемы БД, API эндпоинты, n8n флоу
- `weekN_*_plan.md` — детальный план реализации каждой недели с примерами кода
