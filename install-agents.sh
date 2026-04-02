#!/bin/bash
# Iron Arena — установка агентов для Claude Code
# Запусти: bash install-agents.sh

set -e

AGENTS_DIR="$HOME/.claude/agents"
REPO_DIR="./agency-agents"

echo "=== Iron Arena Agent Setup ==="

# Проверяем что репо скачан
if [ ! -d "$REPO_DIR" ]; then
  echo "Скачиваем agency-agents..."
  git clone https://github.com/msitarzewski/agency-agents.git
fi

# Создаём папку агентов
mkdir -p "$AGENTS_DIR"

echo "Копируем агентов..."

# Оркестратор
cp "$REPO_DIR/specialized/agents-orchestrator.md" "$AGENTS_DIR/"

# Планирование
cp "$REPO_DIR/project-management/project-manager-senior.md" "$AGENTS_DIR/"

# Engineering
cp "$REPO_DIR/engineering/engineering-backend-architect.md" "$AGENTS_DIR/"
cp "$REPO_DIR/engineering/engineering-frontend-developer.md" "$AGENTS_DIR/"
cp "$REPO_DIR/engineering/engineering-senior-developer.md" "$AGENTS_DIR/"
cp "$REPO_DIR/engineering/engineering-rapid-prototyper.md" "$AGENTS_DIR/"
cp "$REPO_DIR/engineering/engineering-security-engineer.md" "$AGENTS_DIR/"

# Design & QA
cp "$REPO_DIR/design/design-ui-designer.md" "$AGENTS_DIR/"
cp "$REPO_DIR/testing/testing-reality-checker.md" "$AGENTS_DIR/"
cp "$REPO_DIR/testing/testing-evidence-collector.md" "$AGENTS_DIR/"

echo ""
echo "Установлено агентов: $(ls $AGENTS_DIR | wc -l)"
echo ""
echo "=== Готово! ==="
echo ""
echo "Следующий шаг:"
echo "  cd iron-arena"
echo "  claude"
echo ""
echo "Потом вставь команду из CLAUDE.md в чат Claude Code"