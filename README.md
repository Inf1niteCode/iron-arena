# Iron Arena — Запуск команды агентов

## Что у тебя есть в этой папке
```
iron-arena/
├── README.md                ← этот файл
├── CLAUDE.md                ← правила команды (Claude Code читает автоматически)
├── install-agents.sh        ← скрипт установки агентов
└── project-specs/
    └── mvp-setup.md         ← полное техзадание для агентов
```

---

## Шаг 1 — Установи Claude Code (если ещё нет)

```bash
npm install -g @anthropic-ai/claude-code
```

Проверь:
```bash
claude --version
```

---

## Шаг 2 — Установи агентов

```bash
bash install-agents.sh
```

Скрипт сам скачает agency-agents и скопирует нужных агентов в `~/.claude/agents/`

---

## Шаг 3 — Запусти Claude Code в папке проекта

```bash
cd iron-arena
claude
```

Claude Code автоматически прочитает `CLAUDE.md` — это "конституция" команды.

---

## Шаг 4 — Запусти оркестратор

Вставь в чат Claude Code:

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

---

## Что будет происходить

```
Project Manager     → создаст план фаз и задачи
        ↓
Backend Architect   → спроектирует API и БД, напишет api-contract.md
        ↓ (параллельно)
Frontend Developer  → построит UI на React + Telegram SDK
Senior Developer    → реализует PvP WebSocket движок
Rapid Prototyper    → быстрые прототипы боёвки и аукциона
UI Designer         → спроектирует все экраны
        ↓
Security Engineer   → проверит PvP на читы, аукцион на уязвимости
        ↓
Reality Checker     → финальное QA, проверит все формулы
```

---

## Как задавать вопросы агентам в процессе

Ты можешь в любой момент написать в Claude Code:

```
Используй Backend Architect и объясни как устроен WebSocket протокол боёв
```

```
Используй Frontend Developer и покажи как подключить Telegram SDK
```

```
Используй Reality Checker и проверь правильность формулы урона
```

---

## Папки которые появятся после запуска

```
iron-arena/
├── reports/
│   ├── pm-plan.md           ← план от Project Manager
│   ├── api-contract.md      ← API контракт (Frontend читает это)
│   ├── db-schema.md         ← схема базы данных
│   ├── ui-screens.md        ← список экранов от UI Designer
│   ├── security-audit.md    ← аудит безопасности
│   └── qa-final.md          ← финальный отчёт QA
├── tasks/
│   ├── frontend-tasks.md
│   ├── backend-tasks.md
│   └── ...
└── src/
    ├── frontend/
    ├── backend/
    └── prototypes/
```