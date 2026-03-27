"""
Combined routers: Simulation, Anomaly Detection, Comparison,
History, Export, Admin, Evaluation, Monitoring
"""
import io
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from app.database import get_db
from app.models.models import (
    Dataset, User, QueryHistory, Simulation,
    EvaluationResult, MonitoringLog
)
from app.utils.auth import get_current_user, require_admin
import pandas as pd
import numpy as np

# ─── Simulation ──────────────────────────────────────────────────────────────
sim_router = APIRouter(prefix="/api/simulate", tags=["What-If Simulation"])


class SimulateRequest(BaseModel):
    dataset_id: Optional[int] = None
    variables: Dict[str, Any]
    scenario_name: str = "Scenario"


@sim_router.post("/")
async def run_simulation(
    payload: SimulateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Run a what-if simulation by modifying variable values."""
    results = {}
    for var, value in payload.variables.items():
        base = float(value)
        results[var] = {
            "base": base,
            "optimistic": round(base * 1.15, 2),
            "pessimistic": round(base * 0.85, 2),
            "delta_pct": 15.0,
        }

    sim = Simulation(
        dataset_id=payload.dataset_id,
        variables=payload.variables,
        results=results,
    )
    db.add(sim)
    await db.commit()
    await db.refresh(sim)

    return {
        "simulation_id": sim.id,
        "scenario_name": payload.scenario_name,
        "variables": payload.variables,
        "results": results,
    }


# ─── Anomaly Detection ───────────────────────────────────────────────────────
anomaly_router = APIRouter(prefix="/api/anomaly", tags=["Anomaly Detection"])


@anomaly_router.get("/{dataset_id}")
async def detect_anomalies(
    dataset_id: int,
    column: str,
    method: str = "zscore",  # zscore | iqr
    threshold: float = 2.5,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Dataset).where(Dataset.id == dataset_id, Dataset.owner_id == current_user.id))
    dataset = result.scalar_one_or_none()
    if not dataset:
        raise HTTPException(404, "Dataset not found")

    df = pd.read_csv(dataset.file_path)
    if column not in df.columns:
        raise HTTPException(400, "Column not found")

    series = df[column].dropna()
    anomaly_mask = pd.Series([False] * len(series), index=series.index)

    if method == "zscore":
        z_scores = np.abs((series - series.mean()) / series.std())
        anomaly_mask = z_scores > threshold
    elif method == "iqr":
        Q1, Q3 = series.quantile(0.25), series.quantile(0.75)
        IQR = Q3 - Q1
        anomaly_mask = (series < Q1 - threshold * IQR) | (series > Q3 + threshold * IQR)

    anomalies = df[anomaly_mask]
    return {
        "column": column,
        "method": method,
        "threshold": threshold,
        "total_rows": len(series),
        "anomaly_count": int(anomaly_mask.sum()),
        "anomaly_pct": round(float(anomaly_mask.mean() * 100), 2),
        "anomalies": anomalies.head(50).to_dict(orient="records"),
    }


# ─── Comparison ──────────────────────────────────────────────────────────────
compare_router = APIRouter(prefix="/api/compare", tags=["Comparison"])


class CompareRequest(BaseModel):
    dataset_id_1: int
    dataset_id_2: int
    column: str


@compare_router.post("/")
async def compare_datasets(
    payload: CompareRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    async def load(dataset_id):
        r = await db.execute(select(Dataset).where(Dataset.id == dataset_id, Dataset.owner_id == current_user.id))
        d = r.scalar_one_or_none()
        if not d:
            raise HTTPException(404, f"Dataset {dataset_id} not found")
        return d

    d1 = await load(payload.dataset_id_1)
    d2 = await load(payload.dataset_id_2)

    df1 = pd.read_csv(d1.file_path)
    df2 = pd.read_csv(d2.file_path)

    def col_stats(df, col):
        if col not in df.columns:
            return None
        s = df[col].dropna()
        return {"mean": round(float(s.mean()), 4), "std": round(float(s.std()), 4),
                "min": round(float(s.min()), 4), "max": round(float(s.max()), 4), "count": len(s)}

    return {
        "dataset_1": {"id": d1.id, "name": d1.name, "stats": col_stats(df1, payload.column)},
        "dataset_2": {"id": d2.id, "name": d2.name, "stats": col_stats(df2, payload.column)},
        "column": payload.column,
    }


# ─── History ─────────────────────────────────────────────────────────────────
history_router = APIRouter(prefix="/api/history", tags=["History"])


@history_router.get("/")
async def get_history(
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(QueryHistory)
        .where(QueryHistory.user_id == current_user.id)
        .order_by(QueryHistory.created_at.desc())
        .limit(limit)
    )
    history = result.scalars().all()
    return [
        {"id": h.id, "query": h.query, "response": h.response[:200] if h.response else "",
         "model_used": h.model_used, "tokens_used": h.tokens_used,
         "latency_ms": h.latency_ms, "created_at": h.created_at}
        for h in history
    ]


# ─── Export ──────────────────────────────────────────────────────────────────
export_router = APIRouter(prefix="/api/export", tags=["Export"])


@export_router.get("/excel/{dataset_id}")
async def export_excel(
    dataset_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Dataset).where(Dataset.id == dataset_id, Dataset.owner_id == current_user.id))
    dataset = result.scalar_one_or_none()
    if not dataset:
        raise HTTPException(404, "Dataset not found")

    df = pd.read_csv(dataset.file_path)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Data")
        df.describe().to_excel(writer, sheet_name="Stats")
    output.seek(0)

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={dataset.name}.xlsx"},
    )


@export_router.get("/csv/{dataset_id}")
async def export_csv(
    dataset_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Dataset).where(Dataset.id == dataset_id, Dataset.owner_id == current_user.id))
    dataset = result.scalar_one_or_none()
    if not dataset:
        raise HTTPException(404, "Dataset not found")

    df = pd.read_csv(dataset.file_path)
    output = io.StringIO()
    df.to_csv(output, index=False)
    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode()),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={dataset.name}"},
    )


# ─── Admin ───────────────────────────────────────────────────────────────────
admin_router = APIRouter(prefix="/api/admin", tags=["Admin"])


@admin_router.get("/users")
async def list_users(db: AsyncSession = Depends(get_db), admin: User = Depends(require_admin)):
    result = await db.execute(select(User))
    users = result.scalars().all()
    return [{"id": u.id, "email": u.email, "username": u.username,
             "role": u.role, "is_active": u.is_active, "created_at": u.created_at}
            for u in users]


@admin_router.delete("/dataset/{dataset_id}", status_code=204)
async def admin_delete_dataset(dataset_id: int, db: AsyncSession = Depends(get_db), admin: User = Depends(require_admin)):
    await db.execute(delete(Dataset).where(Dataset.id == dataset_id))
    await db.commit()


@admin_router.get("/stats")
async def admin_stats(db: AsyncSession = Depends(get_db), admin: User = Depends(require_admin)):
    from sqlalchemy import func
    users_count = await db.execute(select(func.count(User.id)))
    datasets_count = await db.execute(select(func.count(Dataset.id)))
    queries_count = await db.execute(select(func.count(QueryHistory.id)))
    return {
        "total_users": users_count.scalar(),
        "total_datasets": datasets_count.scalar(),
        "total_queries": queries_count.scalar(),
    }


# ─── Evaluation (Ragas-style) ─────────────────────────────────────────────────
eval_router = APIRouter(prefix="/api/evaluate", tags=["Evaluation"])


@eval_router.post("/")
async def evaluate_response(
    query_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Compute mock evaluation scores (plug in Ragas for real scoring)."""
    result = await db.execute(select(QueryHistory).where(QueryHistory.id == query_id, QueryHistory.user_id == current_user.id))
    query = result.scalar_one_or_none()
    if not query:
        raise HTTPException(404, "Query not found")

    # Placeholder scores — replace with actual Ragas evaluation
    scores = {
        "context_recall": round(np.random.uniform(0.7, 0.95), 3),
        "context_precision": round(np.random.uniform(0.7, 0.95), 3),
        "faithfulness": round(np.random.uniform(0.75, 0.98), 3),
        "answer_relevancy": round(np.random.uniform(0.72, 0.96), 3),
    }
    overall = round(float(np.mean(list(scores.values()))), 3)

    eval_result = EvaluationResult(
        query_id=query_id,
        context_recall=scores["context_recall"],
        context_precision=scores["context_precision"],
        faithfulness=scores["faithfulness"],
        answer_relevancy=scores["answer_relevancy"],
        raw_scores=scores,
    )
    db.add(eval_result)
    query.accuracy_score = overall
    query.relevance_score = scores["answer_relevancy"]
    await db.commit()

    return {"query_id": query_id, "scores": scores, "overall": overall}


@eval_router.get("/dashboard")
async def eval_dashboard(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(EvaluationResult).order_by(EvaluationResult.created_at.desc()).limit(20))
    evals = result.scalars().all()
    if not evals:
        return {"message": "No evaluations yet", "avg_scores": {}}

    avg = {
        "context_recall": round(float(np.mean([e.context_recall for e in evals if e.context_recall])), 3),
        "context_precision": round(float(np.mean([e.context_precision for e in evals if e.context_precision])), 3),
        "faithfulness": round(float(np.mean([e.faithfulness for e in evals if e.faithfulness])), 3),
        "answer_relevancy": round(float(np.mean([e.answer_relevancy for e in evals if e.answer_relevancy])), 3),
    }
    return {"total_evaluations": len(evals), "avg_scores": avg}


# ─── Monitoring ───────────────────────────────────────────────────────────────
monitor_router = APIRouter(prefix="/api/monitor", tags=["Monitoring"])


@monitor_router.get("/logs")
async def get_logs(limit: int = 100, db: AsyncSession = Depends(get_db), admin: User = Depends(require_admin)):
    result = await db.execute(select(MonitoringLog).order_by(MonitoringLog.created_at.desc()).limit(limit))
    logs = result.scalars().all()
    return [
        {"id": l.id, "endpoint": l.endpoint, "method": l.method, "status_code": l.status_code,
         "latency_ms": l.latency_ms, "created_at": l.created_at}
        for l in logs
    ]


@monitor_router.get("/summary")
async def monitor_summary(db: AsyncSession = Depends(get_db), admin: User = Depends(require_admin)):
    result = await db.execute(select(MonitoringLog))
    logs = result.scalars().all()
    if not logs:
        return {"message": "No logs yet"}

    latencies = [l.latency_ms for l in logs if l.latency_ms]
    errors = [l for l in logs if l.status_code and l.status_code >= 400]
    return {
        "total_requests": len(logs),
        "error_count": len(errors),
        "error_rate_pct": round(len(errors) / len(logs) * 100, 2),
        "avg_latency_ms": round(float(np.mean(latencies)), 2) if latencies else 0,
        "p95_latency_ms": round(float(np.percentile(latencies, 95)), 2) if latencies else 0,
    }
