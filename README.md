# Adaptive Roadmap Builder

Платформа для построения адаптивных учебных планов на основе графа навыков:
- импорт/валидация графа навыков,
- генерация плана под цель (`surface`/`balanced`/`deep`),
- трекинг прогресса,
- иерархия планов (подпланы от выбранных навыков).

## Стек
- Backend: Python 3.12, FastAPI, SQLAlchemy, Alembic, PostgreSQL
- Frontend: React + TypeScript + Vite
- Инфра: Docker Compose (Postgres, Redis, backend, frontend)

## Структура
- `backend/` — API, доменная логика, репозитории, миграции
- `frontend/` — UI
- `backend/alembic/` — миграции БД
- `docker-compose.yml` — локальный запуск окружения
- `.env.example` — шаблон переменных окружения

## Переменные окружения
Создай `.env` в корне проекта:

```bash
cp .env.example .env
```

Ключевые переменные:
- `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`
- `DATABASE_URL` (используется для локального запуска backend вне Docker)
- `SKILLS_JSON_PATH`
- `JWT_SECRET_KEY`, `JWT_ALGORITHM`
- `ACCESS_TOKEN_EXPIRE_MINUTES`, `REFRESH_TOKEN_EXPIRE_DAYS`

## Запуск через Docker (рекомендуется)
### 1) Подготовка
```bash
cp .env.example .env
```

### 2) Сборка и запуск
```bash
docker compose up --build
```

### 3) Доступ
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs

### 4) Остановка
```bash
docker compose down
```

С удалением volumes (полный сброс данных БД):
```bash
docker compose down -v
```

## Локальный запуск без Docker
### Backend
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
alembic -c backend/alembic.ini upgrade head
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

### Frontend
```bash
cd frontend
npm ci
npm run dev
```

## Миграции Alembic
Из корня проекта:

Применить миграции:
```bash
alembic -c backend/alembic.ini upgrade head
```

Откатить последнюю:
```bash
alembic -c backend/alembic.ini downgrade -1
```

Создать новую миграцию:
```bash
alembic -c backend/alembic.ini revision -m "describe change"
```

## Тесты
Backend:
```bash
cd backend
pytest
```

Frontend:
```bash
cd frontend
npm run test:run
```

## Частые проблемы
1. `alembic`/`uvicorn` не найдены  
Причина: не активировано venv в `backend`.

2. Backend не поднимается в Docker из-за БД  
Проверь `.env` и что порт `5432` не занят.

3. Ошибки авторизации (401)  
Проверь `JWT_SECRET_KEY` и что backend запущен с актуальным `.env`.

## Полезно
- OpenAPI/Swagger: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
