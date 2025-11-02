#!/usr/bin/env bash
#
# Launch Hephaestus workflow for coached-data-explore project
#
# This script bootstraps the coached-data-explore project with Hephaestus,
# creating the initial Phase 1 PRD analysis task and spawning agents.
#
# Usage:
#   ./Mike/coached/launch.sh [--no-clean] [--no-drop-db]
#
# Options:
#   --no-clean     Skip Qdrant cleaning (keep existing memories)
#   --no-drop-db   Skip database drop (keep existing tasks)
#

set -euo pipefail

# Configuration
HEPH_ROOT="/Users/mike/www/ai/hephaestus"
WORKING_DIR="/Users/mike/www/ai/coached-data-explore"
WORKTREES="/tmp/hephaestus_worktrees"
PRD_PATH="/Users/mike/www/ai/coached-data-explore/docs/prds/phase7-multi-audience-discovery-prd.md"

# Parse arguments
CLEAN_QDRANT="--clean-qdrant"
DROP_DB="--drop-db"

for arg in "$@"; do
  case $arg in
    --no-clean)
      CLEAN_QDRANT=""
      ;;
    --no-drop-db)
      DROP_DB=""
      ;;
    *)
      echo "Unknown option: $arg"
      echo "Usage: $0 [--no-clean] [--no-drop-db]"
      exit 1
      ;;
  esac
done

# Verify paths exist
if [ ! -d "$WORKING_DIR" ]; then
  echo "❌ Error: Working directory not found: $WORKING_DIR"
  exit 1
fi

if [ ! -f "$PRD_PATH" ]; then
  echo "❌ Error: PRD not found: $PRD_PATH"
  exit 1
fi

cd "$HEPH_ROOT"

# Verify virtualenv
if [ ! -x "$HEPH_ROOT/.venv/bin/python" ]; then
  echo "❌ Error: Python virtualenv not found at $HEPH_ROOT/.venv"
  echo "Run: python3 -m venv .venv && .venv/bin/pip install -r requirements.txt"
  exit 1
fi

echo "🚀 Launching coached-data-explore with Hephaestus"
echo "================================================"
echo "Working dir: $WORKING_DIR"
echo "Worktrees:   $WORKTREES"
echo "PRD:         $PRD_PATH"
echo "Clean Qdrant: ${CLEAN_QDRANT:-no}"
echo "Drop DB:      ${DROP_DB:-no}"
echo ""

# Create worktrees directory
mkdir -p "$WORKTREES"

# Run bootstrap
.venv/bin/python scripts/bootstrap_project.py \
  --working-dir "$WORKING_DIR" \
  --worktrees "$WORKTREES" \
  --prd "$PRD_PATH" \
  $CLEAN_QDRANT \
  $DROP_DB

echo ""
echo "✅ Bootstrap complete!"
echo ""
echo "📊 Next steps:"
echo "  1. View backend health:  http://localhost:8000/health"
echo "  2. View tasks:           http://localhost:8000/api/tasks"
echo "  3. View tickets board:   http://localhost:8000/tickets"
echo "  4. View frontend:        http://localhost:5173"
echo ""
echo "📝 Monitor logs:"
echo "  tail -f logs/monitor.out"
echo "  tail -f logs/server.out"
echo ""
echo "🛑 To stop services:"
echo "  pkill -f run_monitor.py"
echo "  lsof -ti :8000 | xargs kill"
