#!/bin/bash
# ABHEDYA Full System Health Check
set -uo pipefail

APP_URL=${APP_URL:-"http://localhost:8000"}
RED='[0;31m'; GREEN='[0;32m'; YELLOW='[1;33m'; NC='[0m'

check_service() {
  local name=$1; local cmd=$2; local expected=${3:-0}
  if eval "${cmd}" &>/dev/null; then
    echo -e "  ${GREEN}✓${NC} ${name}"
    return 0
  else
    echo -e "  ${RED}✗${NC} ${name}"
    return 1
  fi
}

echo "===== ABHEDYA Health Check ====="
echo "Timestamp: $(date)"
echo ""
FAILED=0

echo "--- Application ---"
check_service "App liveness" "curl -sf ${APP_URL}/health" || FAILED=$((FAILED+1))
check_service "Platform health" "curl -sf ${APP_URL}/api/v1/platform/health" || FAILED=$((FAILED+1))
check_service "API docs" "curl -sf ${APP_URL}/docs" || FAILED=$((FAILED+1))

echo ""
echo "--- Databases ---"
check_service "PostgreSQL" "pg_isready -h ${POSTGRES_HOST:-localhost} -U ${POSTGRES_USER:-postgres}" || FAILED=$((FAILED+1))
check_service "Redis" "redis-cli -h ${REDIS_HOST:-localhost} ping" || FAILED=$((FAILED+1))
check_service "Neo4j" "curl -sf http://${NEO4J_HOST:-localhost}:7474" || FAILED=$((FAILED+1))

echo ""
if [ $FAILED -eq 0 ]; then
  echo -e "${GREEN}All checks passed.${NC}"
  exit 0
else
  echo -e "${RED}${FAILED} check(s) failed.${NC}"
  exit 1
fi
