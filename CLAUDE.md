# Iron Arena — Правила команды агентов

## Проект
Telegram Mini App браузерная RPG с PvP ареной, инвентарём и аукционом.
Стек: React + TypeScript + FastAPI + PostgreSQL + Redis + WebSocket.

---

## Команда и зоны ответственности

### Agents Orchestrator
- Управляет всей командой
- Читает project-specs/mvp-setup.md перед стартом
- Назначает задачи в правильном порядке (PM → Arch → Dev → QA)
- Проверяет что каждый агент написал свой отчёт в /reports/ перед переходом к следующему

### Project Manager (project-manager-senior)
- Читает mvp-setup.md и создаёт план фаз
- Пишет задачи для каждого разработчика в /tasks/
- Контролирует что фазы выполняются по порядку
- Пишет отчёт в reports/pm-plan.md

### Backend Architect (engineering-backend-architect)
- Проектирует API и схему БД
- ОБЯЗАТЕЛЬНО пишет reports/api-contract.md — Frontend читает этот файл
- ОБЯЗАТЕЛЬНО пишет reports/db-schema.md
- Отвечает за WebSocket протокол для PvP боёв
- НЕ трогает файлы в /src/frontend/

### Frontend Developer (engineering-frontend-developer)
- ЧИТАЕТ reports/api-contract.md перед написанием кода
- Отвечает за всё в /src/frontend/
- Использует Telegram WebApp SDK (@telegram-apps/sdk)
- Drag & drop инвентарь
- НЕ трогает файлы в /src/backend/

### Rapid Prototyper (engineering-rapid-prototyper)
- Делает рабочий прототип боёвки и аукциона максимально быстро
- Приоритет — работающий код, не идеальный
- Пишет в /src/prototypes/ чтобы не сломать основной код

### Senior Developer (engineering-senior-developer)
- Реализует PvP WebSocket движок
- Реализует матчмейкинг
- Пишет сложную бизнес-логику боёвки (урон, уклонение, стамина)
- Код должен быть защищён от читерства (валидация на сервере)

### UI Designer (design-ui-designer)
- Проектирует экраны: профиль, инвентарь, арена, магазин, аукцион
- Все экраны оптимизированы под мобильный Telegram (360px min-width)
- Пишет компоненты в /src/frontend/components/
- Пишет отчёт в reports/ui-screens.md

### Security Engineer (engineering-security-engineer)
- Проверяет что все ходы в PvP валидируются на сервере
- Проверяет авторизацию через Telegram initData
- Проверяет аукцион на двойное списание золота
- Пишет отчёт в reports/security-audit.md

### Reality Checker (testing-reality-checker)
- Запускается ПОСЛЕДНИМ
- Проверяет что все формулы (HP, урон, XP) реализованы правильно
- Проверяет что API контракт совпадает с реализацией
- Пишет reports/qa-final.md — без этого файла проект не считается готовым

---

## Правила совместной работы

### Порядок фаз — строго соблюдать:
```
1. Project Manager → создаёт план → reports/pm-plan.md
2. Backend Architect → API + БД → reports/api-contract.md + reports/db-schema.md
3. Frontend Developer → читает api-contract.md → пишет UI
4. Senior Developer → PvP движок (параллельно с Frontend)
5. Rapid Prototyper → прототипы (параллельно)
6. UI Designer → экраны (параллельно с Frontend)
7. Security Engineer → аудит → reports/security-audit.md
8. Reality Checker → финальная проверка → reports/qa-final.md
```

### Общие файлы (читают все агенты):
- `project-specs/mvp-setup.md` — главное техзадание
- `reports/api-contract.md` — контракт API (Backend пишет, Frontend читает)
- `reports/db-schema.md` — схема БД

### Правила кода:
- Все формулы из mvp-setup.md реализовывать ТОЧНО как написано
- Валидация всей игровой логики ТОЛЬКО на backend, frontend только отображает
- Каждый файл начинается с комментария: кто его создал и зачем
- TypeScript строгий режим (strict: true)

### Структура проекта:
```
iron-arena/
├── CLAUDE.md                    ← этот файл
├── project-specs/
│   └── mvp-setup.md
├── reports/                     ← агенты пишут сюда отчёты
├── tasks/                       ← PM пишет задачи сюда
├── src/
│   ├── frontend/                ← только Frontend Developer и UI Designer
│   │   ├── components/
│   │   ├── pages/
│   │   └── hooks/
│   ├── backend/                 ← только Backend Architect и Senior Developer
│   │   ├── api/
│   │   ├── models/
│   │   ├── websocket/
│   │   └── game_logic/
│   └── prototypes/              ← только Rapid Prototyper
├── docker-compose.yml
└── README.md
```

---

## Команда запуска оркестратора

Вставь это в Claude Code:
```
Please spawn an agents-orchestrator to execute the complete development
pipeline for project-specs/mvp-setup.md

Team: project-manager-senior, engineering-backend-architect,
engineering-frontend-developer, engineering-senior-developer,
engineering-rapid-prototyper, design-ui-designer,
engineering-security-engineer, testing-reality-checker

Run autonomous workflow:
project-manager-senior → engineering-backend-architect →
[engineering-frontend-developer + engineering-senior-developer +
engineering-rapid-prototyper + design-ui-designer (parallel)] →
engineering-security-engineer → testing-reality-checker

Each agent must write their report to /reports/ before the next phase starts.
```