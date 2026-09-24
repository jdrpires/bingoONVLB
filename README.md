# BingoON

> Web application for creating bingo sessions and conducting non-repeating draws.

**Python · Flask · PostgreSQL/SQLite · Pytest · Docker · Gunicorn**

| | |
|---|---|
| **Type** | Web application |
| **Focus** | Stateful game sessions and deterministic operational flow |
| **Architecture** | Flask web app + relational persistence |
| **Status** | Public technical project |

## Overview

BingoON allows organizers to create bingo sessions and conduct rounds while ensuring drawn numbers are not repeated.

The project is intentionally conventional: randomness belongs to application logic and does not require an AI service.

## Architecture

```text
Organizer
   │
   ▼
Flask Web App
   │
   ├── Session / Draw Logic
   └── Persistence
           │
     SQLite / PostgreSQL
```

## Development

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
flask --app app run --port 5002
```

Open `http://localhost:5002`.

## Tests

```bash
pytest
```

## Configuration

- `SECRET_KEY` — protects application sessions and forms.
- `DATABASE_URL` — database connection. SQLite can be used locally; PostgreSQL is recommended for persistent production environments.

## Production

The repository includes Docker and Gunicorn support.

```bash
docker build -t bingo-on .
docker run --rm -p 5002:5002 \
  -e APP_ENV=production \
  -e SECRET_KEY="<generate-a-long-random-secret>" \
  -e DATABASE_URL="sqlite:////tmp/bingo.db" \
  bingo-on
```

For production, configure persistent storage/database infrastructure and use `/health` for service health checks.

## Why this project is public

BingoON is a compact example of stateful web application design, testing, containerization and production configuration.

---

**Jean Pires** · [GitHub](https://github.com/jdrpires) · [Portfolio](https://github.com/jdrpires/jdrpires)
