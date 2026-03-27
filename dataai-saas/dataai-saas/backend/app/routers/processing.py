from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional, List
from app.database import get_db
from app.models.models import Dataset, User
from app.utils.auth import get_current_user
import pandas as pd
import numpy as np

router = APIRouter(prefix="/api/process", tags=["Data Processing"])


class CleanRequest(BaseModel):
    dataset_id: int
    drop_duplicates: bool = True
    fill_missing_strategy: str = "mean"  # mean | median | mode | drop | zero
    columns_to_drop: Optional[List[str]] = []


@router.post("/clean")
async def clean_dataset(
    payload: CleanRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Dataset).where(Dataset.id == payload.dataset_id, Dataset.owner_id == current_user.id))
    dataset = result.scalar_one_or_none()
    if not dataset:
        raise HTTPException(404, "Dataset not found")

    df = pd.read_csv(dataset.file_path)
    original_shape = df.shape

    if payload.drop_duplicates:
        df = df.drop_duplicates()

    if payload.columns_to_drop:
        df = df.drop(columns=[c for c in payload.columns_to_drop if c in df.columns], errors="ignore")

    strategy = payload.fill_missing_strategy
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    if strategy == "mean":
        df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].mean())
    elif strategy == "median":
        df[numeric_cols] = df[numeric_cols].fillna(df[numeric_cols].median())
    elif strategy == "zero":
        df[numeric_cols] = df[numeric_cols].fillna(0)
    elif strategy == "drop":
        df = df.dropna()

    df.to_csv(dataset.file_path, index=False)
    dataset.rows = df.shape[0]
    dataset.columns = df.shape[1]
    dataset.version = dataset.version + 1
    await db.commit()

    return {
        "before": {"rows": original_shape[0], "cols": original_shape[1]},
        "after": {"rows": df.shape[0], "cols": df.shape[1]},
        "duplicates_removed": original_shape[0] - df.shape[0],
        "version": dataset.version,
    }


@router.get("/aggregate/{dataset_id}")
async def aggregate_data(
    dataset_id: int,
    group_by: str,
    agg_column: str,
    agg_func: str = "sum",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Dataset).where(Dataset.id == dataset_id, Dataset.owner_id == current_user.id))
    dataset = result.scalar_one_or_none()
    if not dataset:
        raise HTTPException(404, "Dataset not found")

    df = pd.read_csv(dataset.file_path)
    if group_by not in df.columns or agg_column not in df.columns:
        raise HTTPException(400, "Invalid column names")

    agg_map = {"sum": "sum", "mean": "mean", "count": "count", "max": "max", "min": "min"}
    func = agg_map.get(agg_func, "sum")
    grouped = df.groupby(group_by)[agg_column].agg(func).reset_index()
    return grouped.to_dict(orient="records")


@router.get("/correlations/{dataset_id}")
async def get_correlations(
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
    corr = numeric.corr().fillna(0).to_dict()
    return {"correlations": corr, "columns": numeric.columns.tolist()}
