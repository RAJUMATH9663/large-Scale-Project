import io, base64
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.models import Dataset, User
from app.utils.auth import get_current_user
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard & Charts"])


def fig_to_base64(fig) -> str:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=100)
    buf.seek(0)
    b64 = base64.b64encode(buf.read()).decode()
    plt.close(fig)
    return f"data:image/png;base64,{b64}"


@router.get("/{dataset_id}")
async def get_dashboard(
    dataset_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Dataset).where(Dataset.id == dataset_id, Dataset.owner_id == current_user.id))
    dataset = result.scalar_one_or_none()
    if not dataset:
        raise HTTPException(404, "Dataset not found")

    df = pd.read_csv(dataset.file_path)
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

    kpis = {}
    for col in numeric_cols[:6]:
        kpis[col] = {
            "sum": round(float(df[col].sum()), 2),
            "mean": round(float(df[col].mean()), 2),
            "max": round(float(df[col].max()), 2),
            "min": round(float(df[col].min()), 2),
        }

    return {
        "dataset_id": dataset_id,
        "name": dataset.name,
        "rows": dataset.rows,
        "columns": dataset.columns,
        "kpis": kpis,
        "numeric_columns": numeric_cols,
        "all_columns": df.columns.tolist(),
        "missing_values": df.isnull().sum().to_dict(),
        "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
    }


@router.get("/charts/{dataset_id}/histogram")
async def histogram_chart(
    dataset_id: int,
    column: str,
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

    fig, ax = plt.subplots(figsize=(8, 5))
    sns.histplot(df[column].dropna(), kde=True, ax=ax, color="#6366f1")
    ax.set_title(f"Distribution of {column}")
    ax.set_xlabel(column)
    return {"image": fig_to_base64(fig)}


@router.get("/charts/{dataset_id}/scatter")
async def scatter_chart(
    dataset_id: int,
    x_col: str,
    y_col: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Dataset).where(Dataset.id == dataset_id, Dataset.owner_id == current_user.id))
    dataset = result.scalar_one_or_none()
    if not dataset:
        raise HTTPException(404, "Dataset not found")

    df = pd.read_csv(dataset.file_path)
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.scatterplot(data=df, x=x_col, y=y_col, ax=ax, alpha=0.6, color="#8b5cf6")
    ax.set_title(f"{x_col} vs {y_col}")
    return {"image": fig_to_base64(fig)}


@router.get("/charts/{dataset_id}/correlation")
async def correlation_heatmap(
    dataset_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Dataset).where(Dataset.id == dataset_id, Dataset.owner_id == current_user.id))
    dataset = result.scalar_one_or_none()
    if not dataset:
        raise HTTPException(404, "Dataset not found")

    df = pd.read_csv(dataset.file_path)
    numeric = df.select_dtypes(include=[np.number])
    if numeric.shape[1] < 2:
        raise HTTPException(400, "Need at least 2 numeric columns")

    fig, ax = plt.subplots(figsize=(10, 8))
    sns.heatmap(numeric.corr(), annot=True, fmt=".2f", cmap="coolwarm", ax=ax)
    ax.set_title("Correlation Matrix")
    return {"image": fig_to_base64(fig)}


@router.get("/charts/{dataset_id}/bar")
async def bar_chart(
    dataset_id: int,
    x_col: str,
    y_col: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Dataset).where(Dataset.id == dataset_id, Dataset.owner_id == current_user.id))
    dataset = result.scalar_one_or_none()
    if not dataset:
        raise HTTPException(404, "Dataset not found")

    df = pd.read_csv(dataset.file_path)
    agg = df.groupby(x_col)[y_col].sum().reset_index().head(20)

    fig, ax = plt.subplots(figsize=(10, 5))
    sns.barplot(data=agg, x=x_col, y=y_col, ax=ax, palette="viridis")
    ax.set_title(f"{y_col} by {x_col}")
    plt.xticks(rotation=45, ha="right")
    return {"image": fig_to_base64(fig)}
