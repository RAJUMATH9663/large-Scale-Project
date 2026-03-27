#!/bin/bash
set -e

# ─── Colors ──────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; CYAN='\033[0;36m'; NC='\033[0m'; BOLD='\033[1m'

echo ""
echo -e "${BOLD}${BLUE}╔══════════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}${BLUE}║        DataAI SaaS — Startup Script              ║${NC}"
echo -e "${BOLD}${BLUE}║  AI + LangGraph + OpenRouter + Neo4j + Ragas     ║${NC}"
echo -e "${BOLD}${BLUE}╚══════════════════════════════════════════════════╝${NC}"
echo ""

# ─── Prerequisites Check ─────────────────────────────────────────────────────
echo -e "${CYAN}[1/5] Checking prerequisites...${NC}"

if ! command -v docker &>/dev/null; then
  echo -e "${RED}✗ Docker not found. Install from https://docs.docker.com/get-docker/${NC}"; exit 1
fi
if ! command -v docker-compose &>/dev/null && ! docker compose version &>/dev/null 2>&1; then
  echo -e "${RED}✗ Docker Compose not found.${NC}"; exit 1
fi
echo -e "${GREEN}✓ Docker & Docker Compose found${NC}"

# ─── .env Setup ──────────────────────────────────────────────────────────────
echo -e "${CYAN}[2/5] Setting up environment...${NC}"

if [ ! -f .env ]; then
  cp .env .env
  echo -e "${YELLOW}⚠  .env file created. Add your OPENROUTER_API_KEY to enable live AI.${NC}"
else
  echo -e "${GREEN}✓ .env file exists${NC}"
fi

# ─── Build ───────────────────────────────────────────────────────────────────
echo -e "${CYAN}[3/5] Building Docker images (first run may take 3-5 min)...${NC}"
docker compose build --parallel

# ─── Start ───────────────────────────────────────────────────────────────────
echo -e "${CYAN}[4/5] Starting all services...${NC}"
docker compose up -d

# ─── Wait for services ───────────────────────────────────────────────────────
echo -e "${CYAN}[5/5] Waiting for services to be healthy...${NC}"
echo -n "  PostgreSQL "; for i in {1..30}; do
  docker compose exec -T postgres pg_isready -U dataai &>/dev/null && echo -e " ${GREEN}✓${NC}" && break
  echo -n "."; sleep 2
done

echo -n "  Backend API "; for i in {1..30}; do
  curl -sf http://localhost:8000/health &>/dev/null && echo -e " ${GREEN}✓${NC}" && break
  echo -n "."; sleep 2
done

echo -n "  Frontend    "; for i in {1..30}; do
  curl -sf http://localhost:3000 &>/dev/null && echo -e " ${GREEN}✓${NC}" && break
  echo -n "."; sleep 2
done

# ─── Done ────────────────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}${GREEN}════════════════════════════════════════${NC}"
echo -e "${BOLD}${GREEN}  🚀 DataAI SaaS is running!            ${NC}"
echo -e "${BOLD}${GREEN}════════════════════════════════════════${NC}"
echo ""
echo -e "  ${BOLD}Frontend:${NC}   ${CYAN}http://localhost:3000${NC}"
echo -e "  ${BOLD}API Docs:${NC}   ${CYAN}http://localhost:8000/docs${NC}"
echo -e "  ${BOLD}Neo4j:${NC}      ${CYAN}http://localhost:7474${NC}  (neo4j / neo4j123)"
echo -e "  ${BOLD}Nginx:${NC}      ${CYAN}http://localhost:80${NC}"
echo ""
echo -e "  ${YELLOW}Add OPENROUTER_API_KEY to .env for live AI${NC}"
echo -e "  ${YELLOW}Register at http://localhost:3000/register${NC}"
echo ""
echo -e "  ${BOLD}Useful commands:${NC}"
echo -e "    ${CYAN}docker compose logs -f backend${NC}    # View API logs"
echo -e "    ${CYAN}docker compose down${NC}               # Stop everything"
echo -e "    ${CYAN}docker compose down -v${NC}            # Stop + wipe data"
echo ""
