# Spendmetrics

Ad spend analytics platform for small businesses. Collects leads from all channels and ad spend from all advertising accounts, then calculates CPL per channel and campaign in a single dashboard.

## Stack

| Component | Technology |
|---|---|
| Backend | FastAPI + Python 3.12 |
| Operational DB | PostgreSQL 15 |
| Analytical DB | ClickHouse 24 |
| Orchestration | n8n |
| Monitoring | Prometheus + Grafana |
| Payments | Stripe |

## Architecture

```
Lead sources
  Website form (webhook + UTM)  ─┐
  Telegram bot (start payload)  ─┤
  VK Lead Ads                   ─┼──► FastAPI ──► ClickHouse
  Meta Lead Ads                 ─┘

Ad spend sync
  Yandex Direct  ─┐
  VK Ads         ─┼──► n8n (nightly) ──► FastAPI ──► ClickHouse
  Meta Ads       ─┘

  ClickHouse ──► Grafana dashboards
  FastAPI    ──► Prometheus ──► Grafana monitoring
  FastAPI    ──► n8n ──► Telegram alerts & digests
```

## Quick Start

```bash
cp backend/.env.example backend/.env
# fill in SECRET_KEY

docker-compose up --build
docker-compose exec backend alembic upgrade head
```

| Service | URL |
|---|---|
| API | http://localhost:8000/docs |
| n8n | http://localhost:5678 |
| Grafana | http://localhost:3000 |
| Prometheus | http://localhost:9090 |

## Running Tests

```bash
docker-compose exec backend pytest
```
