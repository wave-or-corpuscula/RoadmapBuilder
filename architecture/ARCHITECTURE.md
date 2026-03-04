# Knowledge Navigator — Architecture & Development Plan

## 1. Технологический стек

| Слой | Технология | Обоснование |
|------|-----------|-------------|
| Backend | Python 3.12 + FastAPI | Async-first, автогенерация OpenAPI, типизация |
| ORM | SQLAlchemy 2.0 (async) | Нативный async, type-safe queries |
| БД | PostgreSQL 16 | JSONB для гибкого хранения графа, надёжность |
| Кэш/очереди | Redis | Кэш тяжёлых вычислений графа |
| Auth | JWT (python-jose) + bcrypt | Stateless, стандарт |
| Frontend | React 18 + TypeScript | Типобезопасность, экосистема |
| State | Zustand | Минималистичен, без бойлерплейта |
| Graph viz | React Flow | Лучший инструмент для DAG в React |
| HTTP client | TanStack Query + Axios | Кэш, loading states, автоинвалидация |
| UI | shadcn/ui + Tailwind CSS | Копируемые компоненты, полный контроль |
| Сборка | Vite | Быстрая разработка |
| Контейнеры | Docker + docker-compose | Воспроизводимость среды |
| Тесты BE | pytest + pytest-asyncio | Стандарт для async FastAPI |
| Тесты FE | Vitest + React Testing Library | Совместимость с Vite |

---

## 2. Архитектура Backend

### 2.1 Слоистая архитектура

```
API Layer (FastAPI Routers)
    │
    ▼
Service Layer (бизнес-логика, оркестрация)
    │
    ▼
Domain Layer (чистые доменные модели, алгоритмы)
    │
    ▼
Repository Layer (абстракция над БД)
    │
    ▼
Infrastructure (SQLAlchemy, Redis, PostgreSQL)
```

**Правило зависимостей**: каждый слой знает только о слое ниже. Domain не знает о БД. Service не знает о HTTP.

### 2.2 Domain Layer — ядро системы

```
domain/
├── skill.py          # Skill entity + value objects
├── skill_graph.py    # SkillGraph — DAG с алгоритмами
├── user_knowledge.py # UserKnowledge — персональное состояние
├── learning_goal.py  # LearningGoal — описание цели
├── learning_plan.py  # LearningPlan — фиксированный план
└── enums.py          # KnowledgeStatus, LearningMode, Difficulty
```

**SkillGraph** — центральная доменная сущность:
- Хранит граф как `dict[str, Skill]` + adjacency list
- Метод `get_subgraph(targets, mode)` — извлечение подграфа по цели
- Метод `topological_sort(subgraph)` — порядок изучения
- Метод `get_transitive_deps(skill_id)` — все транзитивные зависимости
- Метод `compute_depth(skill_id)` — глубина узла для приоритизации

**LearningMode** влияет на `get_subgraph`:
- `SURFACE` — только прямые prerequisites (глубина 1-2)
- `BALANCED` — стандартные транзитивные зависимости
- `DEEP` — все зависимости включая опциональные

### 2.3 Service Layer

```
services/
├── graph_service.py   # CRUD графа, валидация DAG (нет циклов)
├── plan_service.py    # Построение плана: subgraph → sorted strategy
├── user_service.py    # Регистрация, профиль
└── progress_service.py # Обновление UserKnowledge, next step
```

**PlanService.build_plan()** — основной алгоритм:
1. Получить `SkillGraph` из репозитория
2. Получить `UserKnowledge` пользователя
3. Извлечь подграф: `graph.get_subgraph(goal.targets, mode)`
4. Исключить уже `MASTERED` навыки (опционально)
5. Топологическая сортировка подграфа
6. При равных приоритетах: сортировать по `depth ASC`, `difficulty ASC`
7. Зафиксировать `LearningPlan` через репозиторий

### 2.4 Repository Layer

```
repositories/
├── base.py              # Generic CRUD base repository
├── skill_repository.py  # + bulk_upsert для импорта графа
├── plan_repository.py   # + get_active_plan(user_id)
├── user_repository.py
└── knowledge_repository.py
```

Репозитории принимают `AsyncSession` через Dependency Injection.

### 2.5 API Layer

```
api/v1/
├── router.py     # Сборка всех роутеров
├── auth.py       # POST /auth/register, /auth/login, /auth/refresh
├── skills.py     # CRUD /skills, GET /skills/{id}/dependencies
├── graph.py      # GET /graph, POST /graph/validate
├── plans.py      # POST /plans, GET /plans/{id}, PATCH /plans/{id}/rebuild
├── progress.py   # PATCH /plans/{id}/skills/{skill_id}/status
└── users.py      # GET /users/me, PATCH /users/me
```

### 2.6 Схема БД

```sql
-- Навыки
skills (id UUID PK, title, description, difficulty INT, created_at, updated_at)

-- Зависимости навыков (граф)
skill_prerequisites (skill_id UUID FK, prerequisite_id UUID FK, PRIMARY KEY(skill_id, prerequisite_id))

-- Пользователи
users (id UUID PK, email UNIQUE, hashed_password, created_at)

-- Состояние знаний пользователя
user_knowledge (id UUID PK, user_id UUID FK, skill_id UUID FK, status ENUM, updated_at)

-- Планы обучения
learning_plans (id UUID PK, user_id UUID FK, mode ENUM, created_at, graph_version UUID, is_active BOOL)

-- Навыки в плане (упорядоченные)
plan_skills (id UUID PK, plan_id UUID FK, skill_id UUID FK, order_index INT, status ENUM)

-- Цели плана
plan_goals (plan_id UUID FK, skill_id UUID FK)
```

---

## 3. Архитектура Frontend

### 3.1 Feature-Sliced Design (упрощённый)

```
src/
├── features/
│   ├── auth/           # Логин, регистрация
│   ├── graph/          # Визуализация графа навыков
│   ├── plan/           # Создание и просмотр плана
│   └── progress/       # Отслеживание прогресса
├── shared/
│   ├── api/            # Axios instance + TanStack Query hooks
│   ├── types/          # TypeScript типы (генерация из OpenAPI)
│   ├── ui/             # Общие UI компоненты
│   └── hooks/          # useAuth, useCurrentPlan и др.
├── store/              # Zustand stores
├── pages/              # Роуты (React Router)
└── App.tsx
```

### 3.2 Ключевые страницы

| Route | Компонент | Назначение |
|-------|-----------|-----------|
| `/` | `DashboardPage` | Активный план + быстрый прогресс |
| `/graph` | `GraphPage` | Визуализация всего графа навыков |
| `/plan/new` | `PlanWizardPage` | Выбор цели → режим → генерация |
| `/plan/:id` | `PlanDetailPage` | Список навыков + прогресс |
| `/plan/:id/graph` | `PlanGraphPage` | Визуализация подграфа плана |
| `/skills/:id` | `SkillDetailPage` | Детали навыка |
| `/login` | `LoginPage` | Авторизация |

### 3.3 State Management

```
Zustand stores:
├── authStore        { user, token, login(), logout() }
├── planStore        { activePlan, setActivePlan(), updateSkillStatus() }
└── graphStore       { nodes, edges, selectedNode, setSelected() }

TanStack Query (server state):
├── useSkills()
├── usePlan(id)
├── useCreatePlan()
└── useUpdateSkillStatus()
```

### 3.4 Graph Visualization

React Flow с кастомными нодами:
- `SkillNode` — отображает навык: title, difficulty, статус (цвет)
- `StatusEdge` — рёбра зависимостей
- Панель: zoom, fit view, фильтр по статусу
- Layout: `dagre` алгоритм для автоматического расположения DAG

---

## 4. Алгоритм построения плана (детально)

```python
def build_plan(graph: SkillGraph, goals: list[str], mode: LearningMode, knowledge: UserKnowledge) -> list[str]:
    # 1. Собрать все транзитивные зависимости для каждой цели
    all_deps = set()
    for goal_id in goals:
        deps = graph.get_transitive_deps(goal_id, mode)
        all_deps.update(deps)
        all_deps.add(goal_id)

    # 2. Извлечь подграф
    subgraph = graph.subgraph(all_deps)

    # 3. Топологическая сортировка (Kahn's algorithm)
    sorted_skills = topological_sort(subgraph)

    # 4. Приоритизация при равных зависимостях
    # Группировать по "уровню" (все с in_degree=0 после удаления предыдущего уровня)
    # Внутри уровня: сортировать по depth ASC, difficulty ASC

    # 5. Опционально: исключить MASTERED
    return [s for s in sorted_skills if knowledge.get_status(s) != KnowledgeStatus.MASTERED]
```

---

## 5. План разработки (фазы)

### Фаза 0 — Инфраструктура (1-2 дня)
- [ ] docker-compose: postgres, redis, backend, frontend
- [ ] Alembic миграции
- [ ] Базовая конфигурация (pydantic-settings)
- [ ] Vite + React + TypeScript проект
- [ ] CI скелет (GitHub Actions)

### Фаза 1 — Domain Core (2-3 дня)
- [ ] Доменные модели: Skill, SkillGraph, LearningPlan
- [ ] Алгоритм топологической сортировки
- [ ] Алгоритм извлечения подграфа с учётом режима
- [ ] Unit-тесты алгоритмов (без БД)

### Фаза 2 — Backend API (3-4 дня)
- [ ] Auth (register/login/JWT refresh)
- [ ] CRUD навыков + валидация DAG (нет циклов)
- [ ] API построения плана
- [ ] API прогресса (обновление статуса навыка)
- [ ] Интеграционные тесты API

### Фаза 3 — Frontend Base (2-3 дня)
- [ ] Роутинг, auth flow, защищённые роуты
- [ ] TanStack Query setup + API hooks
- [ ] Zustand stores
- [ ] Базовые UI компоненты (shadcn/ui)

### Фаза 4 — Core Features (4-5 дней)
- [ ] Визуализация графа (React Flow + dagre)
- [ ] Wizard создания плана
- [ ] Страница плана со списком навыков
- [ ] Отметка прогресса + "следующий шаг"

### Фаза 5 — Polish (2-3 дня)
- [ ] Кэширование тяжёлых запросов в Redis
- [ ] Экспорт/импорт графа (JSON)
- [ ] Responsive дизайн
- [ ] E2E тесты (Playwright)

---

## 6. Ключевые архитектурные решения

| Решение | Выбор | Альтернатива | Причина |
|---------|-------|--------------|---------|
| DAG хранение | Таблица edges в PostgreSQL | JSONB в одной колонке | Гибкость запросов, индексы |
| Алгоритм сортировки | Kahn's (BFS) | DFS | Проще группировать по уровням |
| Версионирование графа | UUID версии в плане | Полный snapshot | Достаточно для индикации изменений |
| Plan immutability | `is_active` флаг, новый план | In-place update | Сохраняет историю |
| Auth | JWT + Refresh Token | Session | Stateless, подходит для SPA |
| Graph layout | dagre (auto) | Manual positions | DAG с авто-позиционированием |

---

## 7. Переменные окружения

```env
# Backend
DATABASE_URL=postgresql+asyncpg://user:pass@postgres:5432/knowledge_navigator
REDIS_URL=redis://redis:6379
SECRET_KEY=your-secret-key-min-32-chars
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
CORS_ORIGINS=["http://localhost:5173"]

# Frontend
VITE_API_URL=http://localhost:8000/api/v1
```
