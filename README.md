# Spendmetrics

Платформа аналитики рекламных расходов для малого бизнеса. Автоматически собирает заявки из всех каналов и расходы из рекламных кабинетов, считает CPL по каждому каналу и кампании в одном дашборде.

**Проблема:** малый бизнес тратит деньги на рекламу в нескольких каналах, но не понимает какая реклама реально приносит заявки. Яндекс Метрика видит только Директ, Telegram как источник — слепая зона для всех существующих инструментов.

**Решение:** единая платформа с автоматической синхронизацией расходов и сбором заявок из всех каналов, связкой через UTM-метки и расчётом CPL в реальном времени.

---

## Технический стек

| Компонент | Технология |
|---|---|
| Backend | FastAPI + Python 3.12 |
| Операционная БД | PostgreSQL 15 |
| Аналитическая БД | ClickHouse 24 |
| Оркестрация | n8n |
| Мониторинг | Prometheus + Grafana |
| Очереди / кэш | Redis |
| Платежи | Stripe |
| Деплой | Docker Compose → Railway |

---

## Архитектура

```
Источники заявок
  Форма на сайте (webhook + UTM)  ─┐
  Telegram-бот (start payload)    ─┤
  VK Lead Ads                     ─┼──► FastAPI ──► ClickHouse
  Meta Lead Ads                   ─┘

Рекламные расходы
  Яндекс Директ API  ─┐
  VK Ads API         ─┼──► n8n (02:00 ночи) ──► FastAPI ──► ClickHouse
  Meta Ads API       ─┘

Аналитика
  ClickHouse ──► Grafana (бизнес-дашборды)
  FastAPI    ──► Prometheus ──► Grafana (мониторинг)
  FastAPI    ──► n8n ──► Telegram (алерты, дайджесты)
```

Две базы данных с разными ролями: **PostgreSQL** хранит операционные данные (пользователи, OAuth-токены, подписки), **ClickHouse** — аналитику (заявки, расходы, метрики).

---

## Быстрый старт

```bash
git clone https://github.com/your-username/spend-metrics
cd spend-metrics

cp backend/.env.example backend/.env
# заполнить SECRET_KEY в .env

docker-compose up --build
```

После запуска доступны:

| Сервис | URL |
|---|---|
| API | http://localhost:8000 |
| API docs | http://localhost:8000/docs |
| n8n | http://localhost:5678 |
| Grafana | http://localhost:3000 |
| Prometheus | http://localhost:9090 |

Применить миграции БД:

```bash
docker-compose exec backend alembic upgrade head
```

---

## API

### Авторизация

```
POST /auth/register   — регистрация, возвращает JWT-токены
POST /auth/login      — вход
POST /auth/refresh    — обновление access-токена
GET  /auth/me         — профиль текущего пользователя
```

### Заявки

```
POST /webhook/{token} — приём заявки с UTM-метками (для форм на сайте)
```

### Интеграции (в разработке)

```
GET  /oauth/connect/{provider}    — начало OAuth (yandex / vk / meta)
GET  /oauth/callback/{provider}   — обработка callback
GET  /api/connections             — список подключённых кабинетов
DELETE /api/connections/{id}      — отключить кабинет
```

### Аналитика (в разработке)

```
GET /api/stats/overview      — общая статистика
GET /api/stats/by-channel    — CPL по каналам
GET /api/stats/by-campaign   — CPL по кампаниям
GET /api/leads               — список заявок с фильтрами
```

---

## Разработка

```bash
# Запустить тесты
docker-compose exec backend pytest

# Создать миграцию после изменения моделей
docker-compose exec backend alembic revision --autogenerate -m "название"

# Логи бэкенда
docker-compose logs -f backend
```

---

## Статус разработки

| Неделя | Что | Статус |
|---|---|---|
| 1 | FastAPI + PostgreSQL + ClickHouse + JWT + webhook | ✅ Готово |
| 2 | n8n + Telegram уведомления о заявках | 🔲 |
| 3 | Яндекс Директ OAuth + синхронизация расходов | 🔲 |
| 4 | VK Ads + VK Lead Ads + расчёт CPL | 🔲 |
| 5 | Telegram-бот + алерты + еженедельный дайджест | 🔲 |
| 6 | Grafana дашборды + Prometheus мониторинг | 🔲 |
| 7 | Meta Ads + Stripe подписки | 🔲 |
| 8 | Деплой на Railway + лендинг | 🔲 |
