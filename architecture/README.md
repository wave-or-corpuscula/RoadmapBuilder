# Knowledge Navigator

Персональный инструмент для построения управляемых траекторий обучения на основе графа навыков.

## Быстрый старт

```bash
# 1. Клонировать и перейти в директорию
git clone <repo>
cd knowledge-navigator

# 2. Запустить всё через Docker
docker-compose up --build

# 3. Применить миграции БД
docker-compose exec backend alembic upgrade head

# Приложение доступно:
# Frontend: http://localhost:5173
# Backend API: http://localhost:8000
# API Docs (Swagger): http://localhost:8000/docs
```

## Локальная разработка без Docker

### Backend
```bash
cd backend
poetry install
cp .env.example .env   # отредактировать DATABASE_URL, REDIS_URL
alembic upgrade head
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
cp .env.example .env   # VITE_API_URL=http://localhost:8000/api/v1
npm run dev
```

### Тесты
```bash
# Backend unit tests (без БД)
cd backend && pytest tests/ -v

# С покрытием
pytest --cov=app tests/
```

## Структура проекта

```
knowledge-navigator/
├── backend/
│   ├── app/
│   │   ├── domain/          # Доменные модели и алгоритмы (чистый Python)
│   │   │   ├── skill.py
│   │   │   ├── skill_graph.py   ← Основной алгоритмический модуль
│   │   │   ├── learning_plan.py
│   │   │   └── enums.py
│   │   ├── services/        # Бизнес-логика, оркестрация
│   │   │   └── plan_service.py  ← Построение плана
│   │   ├── api/v1/          # FastAPI роутеры
│   │   ├── repositories/    # Абстракция над БД
│   │   ├── schemas/         # Pydantic схемы
│   │   ├── models.py        # SQLAlchemy ORM модели
│   │   ├── core/            # Конфиг, БД, security
│   │   └── main.py
│   ├── alembic/             # Миграции
│   └── tests/               # Тесты (unit + integration)
│
├── frontend/
│   └── src/
│       ├── features/
│       │   ├── graph/       # React Flow визуализация DAG
│       │   └── plan/        # Wizard создания плана
│       ├── shared/
│       │   ├── api/         # Axios + TanStack Query hooks
│       │   └── types/       # TypeScript типы
│       ├── store/           # Zustand stores
│       └── pages/           # Страницы (роуты)
│
├── docker-compose.yml
└── ARCHITECTURE.md          # Детальная архитектурная документация
```

## Ключевые архитектурные принципы

1. **Domain-first**: алгоритмы в `domain/` независимы от БД и HTTP
2. **Immutable plans**: план фиксируется, перестройка — только явное действие
3. **DAG validation**: граф проверяется на отсутствие циклов при каждом изменении
4. **Layered architecture**: API → Service → Domain → Repository
