# 🧠 DataAI SaaS — AI-Powered Data Analytics Platform

> Full-stack SaaS with LangGraph + OpenRouter + Neo4j + Ragas + Scikit-learn

---

## ⚡ Quickstart (One Command)

```bash
# 1. Clone or unzip the project
cd dataai-saas

# 2. Add your OpenRouter API key (optional — works in demo mode without it)
nano .env   # set OPENROUTER_API_KEY=your-key

# 3. Start everything
./start.sh
```

That's it. Open **http://localhost:3000** and register.

---

## 🌐 URLs

| Service | URL | Notes |
|---------|-----|-------|
| Frontend | http://localhost:3000 | React app |
| API | http://localhost:8000 | FastAPI |
| API Docs | http://localhost:8000/docs | Swagger UI |
| Neo4j Browser | http://localhost:7474 | neo4j / neo4j123 |
| Nginx | http://localhost:80 | Reverse proxy |

---

## 🏗 Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Frontend  │────▶│   Nginx     │────▶│   FastAPI   │
│  React+Vite │     │  (port 80)  │     │  (port 8000)│
└─────────────┘     └─────────────┘     └──────┬──────┘
                                                │
              ┌─────────────────────────────────┤
              │             │                   │
       ┌──────▼──────┐ ┌────▼────┐ ┌────────────▼──────┐
       │  PostgreSQL │ │  Neo4j  │ │   Redis (cache)   │
       │  (port 5432)│ │  (7687) │ │   (port 6379)     │
       └─────────────┘ └─────────┘ └───────────────────┘
```

### AI Pipeline (LangGraph Flow)
```
User Query → Intent Detection → Tool Selection → OpenRouter LLM
    → Response + Story → Ragas Evaluation → Opik Monitoring
```

---

## 📦 Tech Stack

### Backend
| Tool | Purpose |
|------|---------|
| **FastAPI** | Web framework |
| **LangGraph** | AI workflow orchestration |
| **OpenRouter** | Multi-model LLM access (GPT-4o, Claude, Gemini, Llama) |
| **Neo4j** | Graph database for relationship analysis |
| **Ragas** | AI response evaluation (accuracy, relevance) |
| **Opik** | LLM monitoring & observability |
| **Pandas + NumPy** | Data processing |
| **Scikit-learn** | ML predictions (Linear, RF, GBM) |
| **Matplotlib + Seaborn** | Chart generation |
| **PostgreSQL** | Main relational database |
| **Redis** | Caching |
| **SQLAlchemy** | Async ORM |

### Frontend
| Tool | Purpose |
|------|---------|
| **React 18** | UI framework |
| **Vite** | Build tool |
| **TailwindCSS** | Styling |
| **Recharts** | Interactive charts |
| **React Query** | Data fetching + caching |
| **Zustand** | State management |
| **React Router v6** | Routing |

---

## 📡 Complete API Reference

### Auth
```
POST   /api/auth/register     Register user
POST   /api/auth/login        Login → JWT token
GET    /api/auth/profile      Get current user
```

### Datasets
```
POST   /api/datasets/upload         Upload CSV/PDF
GET    /api/datasets/               List my datasets
GET    /api/datasets/{id}           Get dataset details
GET    /api/datasets/{id}/stats     Column stats
DELETE /api/datasets/{id}           Delete
```

### Data Processing
```
POST   /api/process/clean           Clean data (missing values, duplicates)
GET    /api/process/aggregate/{id}  Group-by aggregation
GET    /api/process/correlations/{id} Correlation matrix
```

### AI (LangGraph + OpenRouter)
```
POST   /api/ai/query     AI query on your data
GET    /api/ai/models    List available models
```

### Dashboard & Charts
```
GET    /api/dashboard/{id}                    KPIs
GET    /api/dashboard/charts/{id}/histogram   Histogram
GET    /api/dashboard/charts/{id}/scatter     Scatter plot
GET    /api/dashboard/charts/{id}/correlation Heatmap
GET    /api/dashboard/charts/{id}/bar         Bar chart
```

### Graph (Neo4j)
```
POST   /api/graph/build    Build graph from dataset
POST   /api/graph/query    Run Cypher query
GET    /api/graph/stats    Node/edge counts
GET    /api/graph/network  Get network data
```

### Predictions (ML)
```
POST   /api/predict/train     Train model (Linear/RF/GBM)
GET    /api/predict/{id}      List predictions
```

### Simulation
```
POST   /api/simulate/    Run what-if simulation
```

### Anomaly Detection
```
GET    /api/anomaly/{id}     Detect anomalies (Z-score / IQR)
```

### History & Export
```
GET    /api/history/          Query history
GET    /api/export/excel/{id} Export to Excel
GET    /api/export/csv/{id}   Export to CSV
```

### Evaluation (Ragas)
```
POST   /api/evaluate/      Score an AI response
GET    /api/evaluate/dashboard  Avg scores
```

### Monitoring (Opik)
```
GET    /api/monitor/logs     Recent requests
GET    /api/monitor/summary  Error rate, latency
```

### Admin
```
GET    /api/admin/users              List all users
GET    /api/admin/stats              Platform stats
DELETE /api/admin/dataset/{id}       Delete any dataset
```

---

## 🔑 Configuration (.env)

```env
# Required for live AI
OPENROUTER_API_KEY=sk-or-...

# Optional — change passwords in production
POSTGRES_PASSWORD=dataai123
NEO4J_PASSWORD=neo4j123
SECRET_KEY=your-32-char-secret

# Default LLM model
DEFAULT_MODEL=openai/gpt-4o-mini

# Available models via OpenRouter:
# openai/gpt-4o, openai/gpt-4o-mini
# anthropic/claude-3-5-sonnet
# google/gemini-flash-1.5
# meta-llama/llama-3-8b-instruct
```

---

## 🛠 Development Commands

```bash
# Start all services
docker compose up -d

# Watch backend logs
docker compose logs -f backend

# Watch all logs
docker compose logs -f

# Rebuild after code changes
docker compose up -d --build backend

# Open psql
docker compose exec postgres psql -U dataai -d dataai

# Open Neo4j shell
docker compose exec neo4j cypher-shell -u neo4j -p neo4j123

# Stop everything
docker compose down

# Stop + wipe all data (full reset)
docker compose down -v
```

---

## 📁 Project Structure

```
dataai-saas/
├── docker-compose.yml          # All services
├── .env                        # Configuration
├── start.sh                    # One-click startup
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py                 # FastAPI app + middleware
│   └── app/
│       ├── config.py           # Settings
│       ├── database.py         # SQLAlchemy async
│       ├── models/models.py    # DB models
│       ├── utils/
│       │   ├── auth.py         # JWT auth
│       │   └── neo4j_client.py # Neo4j driver
│       └── routers/
│           ├── auth.py         # Authentication
│           ├── datasets.py     # File upload
│           ├── processing.py   # Pandas processing
│           ├── graph.py        # Neo4j graph
│           ├── ai.py           # LangGraph + OpenRouter
│           ├── dashboard.py    # Charts + KPIs
│           ├── prediction.py   # Scikit-learn ML
│           └── misc.py         # Simulation, anomaly, history, export, admin
│
├── frontend/
│   ├── Dockerfile
│   ├── index.html
│   └── src/
│       ├── main.jsx            # React entry
│       ├── App.jsx             # Router
│       ├── index.css           # Global styles
│       ├── store/authStore.js  # Zustand auth
│       ├── services/api.js     # All API calls
│       ├── components/
│       │   ├── Layout.jsx      # App shell
│       │   ├── Sidebar.jsx     # Navigation
│       │   └── UI.jsx          # Design system
│       └── pages/
│           ├── Auth.jsx        # Login / Register
│           ├── Dashboard.jsx   # Main dashboard
│           ├── Datasets.jsx    # Upload + manage
│           ├── Chat.jsx        # AI chat
│           └── OtherPages.jsx  # All other 9 pages
│
└── nginx/
    └── nginx.conf              # Reverse proxy
```

---

## 🚀 Production Deployment

```bash
# Set secure values in .env
SECRET_KEY=$(openssl rand -hex 32)
POSTGRES_PASSWORD=$(openssl rand -hex 16)
NEO4J_PASSWORD=$(openssl rand -hex 16)

# Build optimised images
docker compose -f docker-compose.yml build

# Deploy
docker compose up -d
```

---

## 📝 First Steps After Setup

1. **Register** at http://localhost:3000/register
2. **Upload a CSV** on the Datasets page
3. **Go to Dashboard** — pick your dataset to see KPIs and charts
4. **AI Chat** — ask questions about your data
5. **Predictions** — train an ML model on any numeric column
6. **Simulation** — run what-if scenarios
7. **Graph** — build a Neo4j graph from your dataset

---

Built with ❤️ — DataAI SaaS
